"""단말이 내보낸 실제 JSONL만 집계. 합성 TTFF나 개선률을 생성하지 않는다."""
import argparse,csv,json,math,statistics,re
from pathlib import Path
MODES={'baseline','assisted','assisted_network'}
def read_trials(path):
    starts={};ends={}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        row=json.loads(line)
        if not isinstance(row,dict):raise ValueError('JSON 객체 필요')
        event=row.get('event'); key=row.get('trial_id')
        if event not in {'trial_start','trial_end'}:continue
        if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',key) or row.get('mode') not in MODES:raise ValueError('시험 ID/모드 오류')
        target=starts if event=='trial_start' else ends
        if key in target:raise ValueError('중복 시험 이벤트')
        for name in ['engine_ttff_ms','request_to_gps_ms']:
            v=row.get(name)
            if v is not None and (type(v) not in (int,float) or not 0<=v<=120500 or not math.isfinite(v)):raise ValueError('시간 값 오류')
        if event=='trial_end' and row.get('reason') not in {'first_fix','user_stop','timeout','mock_detected','start_error','callback_registration_failed','provider_disabled','activity_hidden'}:raise ValueError('종료 사유 오류')
        target[key]=row
    if not starts:raise ValueError('실제 시험 시작 로그 없음')
    if set(ends)-set(starts):raise ValueError('시작 없는 종료')
    result=[]
    for key,start in starts.items():
        end=ends.get(key,{})
        if end and start['mode']!=end['mode']:raise ValueError('모드 불일치')
        valid=(end.get('eligible_first_fix') is True and end.get('reason')=='first_fix' and end.get('mock_seen') is False and end.get('log_failed') is False and end.get('engine_started_observed') is True and end.get('engine_ttff_ms') is not None and end.get('request_to_gps_ms') is not None)
        result.append(dict(trial_id=key,mode=start['mode'],reason=end.get('reason','interrupted_no_end'),eligible_first_fix=valid,engine_ttff_ms=end.get('engine_ttff_ms'),request_to_gps_ms=end.get('request_to_gps_ms'),engine_session_origin_verified=False))
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=read_trials(a.input)
    if a.out.exists():p.error('기존 결과 폴더를 덮어쓰지 않습니다')
    a.out.mkdir(parents=True)
    with (a.out/'trials.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary={}
    for mode in sorted(MODES):
        group=[r for r in rows if r['mode']==mode]; times=sorted(r['engine_ttff_ms'] for r in group if r['eligible_first_fix'])
        summary[mode]={'attempts':len(group),'eligible_fixes':len(times),'failures_or_excluded':len(group)-len(times),'median_ttff_ms':statistics.median(times) if times else None,'p95_nearest_rank_ms':times[math.ceil(.95*len(times))-1] if times else None}
    payload={'source':str(a.input),'summary':summary,'causal_acceleration_proven':False,'note':'워밍·순서·보조정보 캐시 이월 및 엔진 시작 확인 없이는 개선 인과관계를 확정하지 않는다.'}
    (a.out/'summary.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(payload,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
