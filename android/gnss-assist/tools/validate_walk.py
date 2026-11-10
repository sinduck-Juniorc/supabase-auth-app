"""이동 관찰 로그 검증. 통신 가속이나 연속 연결을 자동 판정하지 않는다."""
import argparse,json
from pathlib import Path

def validate(rows):
    issues=[];sessions={}
    for e in rows:
        for key in ('event','session_id','elapsed_ms','wall_utc_ms'):
            if key not in e: raise ValueError('필수 필드 누락: '+key)
        if not isinstance(e['elapsed_ms'],int):raise ValueError('잘못된 단조 시각')
        sessions.setdefault(e['session_id'],[]).append(e)
    results=[]
    for key,events in sessions.items():
        errors=[];warnings=[]
        if any(a['elapsed_ms']>b['elapsed_ms'] for a,b in zip(events,events[1:])):errors.append('단조 시각 역전')
        if any(abs((b['wall_utc_ms']-a['wall_utc_ms'])-(b['elapsed_ms']-a['elapsed_ms']))>1000 for a,b in zip(events,events[1:])):warnings.append('벽시계 변화 또는 시각 불일치')
        def get(name):return [e for e in events if e['event']==name]
        starts,ends,ready,indoor=map(get,('observation_start','observation_end','outdoor_location_ready','indoor_arrival'))
        if len(starts)!=1 or len(ends)!=1:errors.append('시작·종료가 각각 하나가 아님')
        if starts and events[0]!=starts[0]:errors.append('시작 이전 이벤트 존재')
        if starts and ends and ready and indoor:
            if not starts[0]['elapsed_ms']<=ready[0]['elapsed_ms']<=indoor[0]['elapsed_ms']<=ends[0]['elapsed_ms']:errors.append('준비·이동·종료 순서 오류')
        if not ready or not indoor:warnings.append('실외 준비 또는 실내 도착 미완료')
        snaps=get('network_snapshot')
        indoor_snaps=[e for e in snaps if indoor and e['elapsed_ms']>=indoor[0]['elapsed_ms']]
        if not indoor_snaps:warnings.append('실내 통신 표본 없음')
        if ends and not ends[0].get('cleanup_success'):warnings.append('해제 성공 미확인')
        seq=[e.get('sequence') for e in events]
        if any(n is not None for n in seq) and seq!=list(range(1,len(events)+1)):errors.append('이벤트 순번 누락·중복')
        results.append({'session_id':key,'structurally_valid':not errors,'errors':errors,'warnings':warnings,'events':len(events),'network_samples':len(snaps),'indoor_network_samples':len(indoor_snaps),'total_ms':ends[0]['elapsed_ms']-starts[0]['elapsed_ms'] if starts and ends else None,'indoor_ms':ends[0]['elapsed_ms']-indoor[0]['elapsed_ms'] if ends and indoor else None,'acceleration_proven':False})
    if not rows:raise ValueError('빈 로그')
    return results

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    result=validate([json.loads(line) for line in a.input.read_text(encoding='utf-8-sig').splitlines() if line.strip()])
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if a.out:a.out.write_text(text+'\n',encoding='utf-8')
    print(text)
