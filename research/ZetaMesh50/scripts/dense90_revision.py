"""밀집 스케줄 튜닝 선택과 독립 평가 보고서. 기존 정책 함수는 변경하지 않는다."""
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scripts.make_report import interval, md_table, setup_font
from simulator.runtime import ROOT

R = ROOT / 'revisions/dense90'

def freeze():
    if (R/'selection.json').exists():
        raise RuntimeError('이미 동결됨: 평가 후 재선택 금지')
    plan = json.loads((R/'plan.json').read_text())
    rows=[]
    for scan, adv in plan['variants']:
        name=f'scan{round(scan*1000)}_adv{round(adv*1000)}'
        p=R/f'tuning_{name}/runs.csv'
        d=pd.read_csv(p)
        assert len(d)==10 and set(d.seed)==set(plan['tuning_seeds'])
        n,mean,low,high=interval(d.success_rate)
        rows.append(dict(variant=name,success=mean,ci_low=low,ci_high=high,energy_j=d.energy_j.mean(),p95_s=d.latency_p95_s.mean(),csv_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    table=pd.DataFrame(rows); table.to_csv(R/'tuning_summary.csv',index=False)
    eligible=table[(table.success>=.94)&(table.ci_low>=.90)].sort_values(['energy_j','p95_s'])
    if eligible.empty: raise RuntimeError('튜닝 기준 충족 후보 없음. 평가하지 않음')
    name=eligible.iloc[0].variant
    old=yaml.safe_load((R/'configs/original.yaml').read_text()); new=yaml.safe_load((R/f'configs/{name}.yaml').read_text())
    diff={k:[old[k],new[k]] for k in old if old[k]!=new[k]}
    assert set(diff)<= {'low_scan_window_s','slow_adv_s'}
    p=ROOT/'configs/50nodes_dense.yaml'; content=p.read_text()
    for k,(_,v) in diff.items():
        content=content.replace(f'{k}: {old[k]}',f'{k}: {v}')
    p.write_text(content)
    selection={'frozen_utc':datetime.now(timezone.utc).isoformat(),'selected':name,'changes':diff,'evaluation_seeds':plan['evaluation_seeds'],'baseline':'fixed','tuning_result':eligible.iloc[0].to_dict(),'config_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'algorithm_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['policies','simulator'] for p in sorted((ROOT/folder).glob('*.py'))}}
    (R/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2))
    print(json.dumps(selection,ensure_ascii=False,indent=2))

def report():
    import matplotlib.pyplot as plt
    setup_font()
    plan=json.loads((R/'plan.json').read_text()); chosen=json.loads((R/'selection.json').read_text())
    data=pd.read_csv(R/'evaluation/runs.csv'); old=pd.read_csv(R/'evaluation_original/runs.csv')
    assert len(data)==240 and len(old)==30 and set(data.nodes)=={50}
    assert set(data.seed)==set(plan['evaluation_seeds'])
    for _,g in data.groupby('policy'): assert len(g)==30 and set(g.seed)==set(plan['evaluation_seeds'])
    assert pd.concat([data,old]).groupby('seed').environment_fingerprint.nunique().max()==1
    for path,digest in chosen['algorithm_sha256'].items(): assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest
    assert hashlib.sha256((ROOT/'configs/50nodes_dense.yaml').read_bytes()).hexdigest()==chosen['config_sha256']
    assert np.allclose(data.energy_j,data[['donor_j','relay_j','seeker_j']].sum(axis=1))
    assert np.allclose(data.energy_j,data[[f'{s}_j' for s in ['tx','rx','scan','idle','sleep','cpu','gnss']]].sum(axis=1))
    old=old.copy(); old['policy']='combined_original'; all_data=pd.concat([old,data],ignore_index=True)
    fields=['success_rate','energy_j','latency_p95_s','penalized_latency_p95_s','donor_j','relay_j','seeker_j','scan_j','tx_j','rx_j','cpu_j','gnss_j','idle_j','sleep_j']
    summaries=[]
    for policy,g in all_data.groupby('policy',sort=False):
        for metric in fields:
            n,mean,low,high=interval(g[metric]); summaries.append(dict(policy=policy,metric=metric,n=n,mean=mean,ci95_low=low,ci95_high=high))
    pd.DataFrame(summaries).to_csv(R/'summary.csv',index=False)
    new=data[data.policy=='combined'].set_index('seed').sort_index()
    raw=[]; paired=[]
    for label,base in [('original',old),('fixed',data[data.policy=='fixed']),('cheb_only',data[data.policy=='cheb_only']),('zeta_only',data[data.policy=='zeta_only']),('lut',data[data.policy=='lut']),('threshold',data[data.policy=='threshold'])]:
        base=base.set_index('seed').sort_index()
        effects={'success_delta_pp':100*(new.success_rate-base.success_rate),'energy_delta_j':new.energy_j-base.energy_j,'energy_reduction_pct':100*(1-new.energy_j/base.energy_j),'latency_delta_s':new.latency_p95_s-base.latency_p95_s,'latency_relative_increase_pct':pd.Series(np.where(base.latency_p95_s>0,100*(new.latency_p95_s/base.latency_p95_s-1),np.where(new.latency_p95_s==0,0,np.inf)),index=new.index)}
        for metric,vals in effects.items():
            n,mean,low,high=interval(vals) if np.isfinite(vals).all() else (len(vals),float('inf'),float('nan'),float('nan')); paired.append(dict(baseline=label,metric=metric,n=n,mean=mean,ci95_low=low,ci95_high=high))
            raw.extend(dict(baseline=label,metric=metric,seed=seed,value=v) for seed,v in vals.items())
    pd.DataFrame(paired).to_csv(R/'paired_summary.csv',index=False); pd.DataFrame(raw).to_csv(R/'paired_raw.csv',index=False)
    tables=all_data.groupby('policy',sort=False)[['success_rate','energy_j','latency_p95_s','donor_j','relay_j','seeker_j']].mean().reset_index(); tables.to_csv(R/'main_table.csv',index=False)
    figdir=R/'figures'; figdir.mkdir(exist_ok=True)
    components=all_data.groupby('policy',sort=False)[[f'{s}_j' for s in ['tx','rx','scan','idle','sleep','cpu','gnss']]].mean()
    components.to_csv(R/'energy_components.csv')
    fig,ax=plt.subplots(figsize=(9,4)); components.loc[['combined_original','combined']].plot.bar(stacked=True,ax=ax); ax.set_ylabel('전체 에너지 구성 [J]'); fig.tight_layout(); fig.savefig(figdir/'energy_components.png'); plt.close(fig)
    for metric,title,scale in [('success_rate','데드라인 내 성공률 [%]',100),('energy_j','전체 에너지 [J]',1),('latency_p95_s','성공 요청 p95 지연 [s]',1)]:
        fig,ax=plt.subplots(figsize=(10,4)); ss=[x for x in summaries if x['metric']==metric]; means=np.array([x['mean'] for x in ss])*scale; errors=np.array([x['ci95_high']-x['mean'] for x in ss])*scale
        ax.bar([x['policy'] for x in ss],means,yerr=errors,capsize=3); ax.set_ylabel(title); ax.tick_params(axis='x',rotation=30)
        if metric=='success_rate': ax.axhline(90,color='red',linestyle='--'); ax.set_ylim(0,105)
        fig.tight_layout(); fig.savefig(figdir/f'{metric}.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4)); ax.plot(new.index,old.set_index('seed').sort_index().success_rate*100,label='수정 전'); ax.plot(new.index,new.success_rate*100,label='수정 후'); ax.axhline(90,color='red',linestyle='--'); ax.set_ylabel('성공률 [%]'); ax.set_xlabel('독립 평가 시드'); ax.legend(); fig.tight_layout(); fig.savefig(figdir/'paired_success.png'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4)); tables.set_index('policy')[['donor_j','relay_j','seeker_j']].plot.bar(stacked=True,ax=ax); ax.set_ylabel('역할별 에너지 [J]'); fig.tight_layout(); fig.savefig(figdir/'role_energy.png'); plt.close(fig)
    n,mean,low,high=interval(new.success_rate)
    fixed={x['metric']:x for x in paired if x['baseline']=='fixed'}
    decision={'mean_success':mean,'ci95':[low,high],'min_seed_success':float(new.success_rate.min()),'seeds_below_90':int((new.success_rate<.9).sum()),'target_mean_90_pass':bool(mean>=.9),'lower_ci_90_pass':bool(low>=.9),'original_three_conditions_mean_pass':bool(fixed['energy_reduction_pct']['mean']>=10 and fixed['success_delta_pp']['mean']>=-2 and fixed['latency_relative_increase_pct']['mean']<=5),'hardware_measured':False}
    (R/'decision.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2))
    manifest=json.loads((R/'evaluation/manifest.json').read_text())
    text=f'''# 밀집 50노드 성공률 개선 검증\n\n설정 변경: `{chosen['changes']}`. 제타 순위 선택·최소 탐색확률·체비쇼프 계수/차수/Clenshaw·중계·TTL·만료·데드라인·PHY는 변경하지 않았다. 같은 밀집 YAML을 모든 정책에 적용했다. threshold/LUT에도 같은 스케줄 설정을 제공한다.\n\n## 설계와 실행\n\n`plan.json`의 사전 선택 규칙으로 튜닝 300~309에서 6설정을 비교하고 `selection.json`에 동결했다. 이후 새 평가 2000~2029에서 8정책 240회와 수정 전 combined 30회를 실행했다. 이전 1000~1029 결과에 다시 맞추지 않았다. 모든 paired 비교에서 환경 fingerprint가 일치했다. 기존 기준선 fixed를 유지했다. CI는 독립 시드별 값/paired 차이에 대한 양측 Student-t 95% CI다. 요청을 독립 표본으로 간주하지 않았다.\n\n실행 환경: {manifest['actual_environment']['os']}, {manifest['actual_environment']['cpu']}, 2프로세스. Windows 5600X 및 UNO R4 실측 결과가 아니다. 평가 벽시계 {manifest['wall_s']:.2f}초. 이벤트 수·실행별 RAM·시드·코드 해시는 각 runs.csv와 manifest.json에 있다.\n\n## 50노드 평가 평균\n\n{md_table(tables)}\n\n성공률 열은 0~1 비율이다. 수정 후 평균 성공률 {100*mean:.2f}%, 95% CI [{100*low:.2f}, {100*high:.2f}]%, 시드별 최저 {100*new.success_rate.min():.2f}%, 90% 미만 시드 {decision['seeds_below_90']}/30.\n\n## paired 차이와 초기 성공 조건\n\n{md_table(pd.DataFrame(paired))}\n\n평균값 기준 원래 세 조건 동시 충족: {decision['original_three_conditions_mean_pass']}. CI와 개별 시드 변동을 함께 판단해야 하며 다른 토폴로지에서 90%를 보장하지 않는다. `lut`, `threshold`가 비슷하거나 우수하면 통합 정책의 추가 복잡도를 정당화하지 않는다.\n\n## 원인과 한계\n\n{md_table(components.loc[['combined_original','combined']].reset_index())}\n\n이번 평가에서 단순 LUT/threshold의 평균 에너지·성공률·지연이 통합 정책보다 좋았다. 90% 목표 달성은 제타·체비쇼프의 우월성 증거가 아니며 추가 복잡도를 정당화하지 않는다. 핵심 아이디어 보존 요청에 따라 선택 알고리즘을 단순 정책으로 교체하지 않았다.\n\n기준선 p95가 0이고 통합 p95가 양수이면 상대 악화율은 무한대로 기록하고 평균 성공 조건을 통과시키지 않는다. 둘 다 0이면 변화율은 0이다. 비유한 상대 변화율은 CI를 계산하지 않으며 표의 미정 표기와 CSV 원값을 함께 확인한다.\n\n변경은 과도한 광고 절전을 완화해 신선한 패킷의 재공급 기회를 늘리는 것이다. 더 잦은 광고가 TX 비용을 늘리더라도, 신선한 패킷을 유지하면 긴 탐색 스캔으로 복귀하는 시간이 줄어 전체 에너지가 감소할 수 있다. 상태별 원자료로 확인해야 하며 추론 연산 비용 감소와 혼동하지 않는다. 에너지는 미실측 전류 가정값이다. p95는 성공한 요청의 지연이며 실패를 deadline으로 대체한 p95도 summary.csv에 보고했다. 등산로/도심 설정과 원래 보고서는 보존했다. 이번 범위는 밀집 설정 수정이며 다른 두 시나리오와 전류 민감도 실험은 재실행하지 않았다. R4 펌웨어의 실제 무선 성능 개선을 검증한 결과가 아니다.\n\n## Windows 재현\n\n프로젝트 루트에서 기존 고정 의존성을 설치한 뒤 실행한다. 새 출력 폴더를 사용한다.\n\n```powershell\n.\\.venv\\Scripts\\python.exe -m pytest -q\n.\\.venv\\Scripts\\python.exe -m scripts.run_experiment --phase evaluation --config configs/50nodes_dense.yaml --seed-start 2000 --seeds 30 --workers 4 --out outputs/dense90_replay\n.\\.venv\\Scripts\\python.exe -m scripts.run_experiment --phase evaluation --config revisions/dense90/configs/original.yaml --policy combined --seed-start 2000 --seeds 30 --workers 4 --out outputs/dense90_original_replay\n```\n\n`MPLCONFIGDIR`을 쓰기 가능한 경로로 설정하고 `python -m scripts.dense90_revision report`로 제공된 원자료의 보고서/그림을 재생성한다. 평가 후 freeze를 재실행하면 오류가 난다. 새 튜닝은 새 연구 디렉터리와 미사용 평가 시드로 진행한다.\n\n## 다음 실물 검증\n\nR4 한 대 광고/스캔 로그를 수집하고, 3노드를 확보하면 동일 광고 간격 비교에서 실제 수신률·보드 전류·기한 내 전달을 측정한다. GNSS 주입/TTFF는 별도 검증한다.\n'''
    (R/'REPORT_ko.md').write_text(text)
    print(json.dumps(decision,ensure_ascii=False,indent=2)); print(tables.to_string(index=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','report']); args=p.parse_args()
    freeze() if args.action=='freeze' else report()
