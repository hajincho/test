using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Game.ThirdPerson;

public static class DayMapNav{
    static readonly Vector2Int[] steps={new Vector2Int(1,0),new Vector2Int(0,1),new Vector2Int(-1,0),new Vector2Int(0,-1),new Vector2Int(1,1),new Vector2Int(1,-1),new Vector2Int(-1,1),new Vector2Int(-1,-1)};
    static readonly Dictionary<Vector2Int,bool> cells=new Dictionary<Vector2Int,bool>();
    static readonly Collider[] hits=new Collider[32];
    static Terrain[] ts;static ThirdPersonMotor motor;static Vector3 spawn;
    public static void Init(ThirdPersonMotor m){motor=m;spawn=m.transform.position;ts=Terrain.activeTerrains.Where(t=>t.terrainData.size.x>900).ToArray();cells.Clear();Physics.SyncTransforms();}
    static bool Free(Vector2Int c){
        if(cells.TryGetValue(c,out var f))return f;
        var p=spawn+new Vector3(c.x,0,c.y);var t=ts.First(a=>p.x>=a.transform.position.x&&p.x<a.transform.position.x+1000&&p.z>=a.transform.position.z&&p.z<a.transform.position.z+1000);var td=t.terrainData;var local=p-t.transform.position;
        p.y=t.SampleHeight(p)+t.transform.position.y;
        f=td.GetSteepness(local.x/1000,local.z/1000)<34f&&p.y>-37.3f;
        if(f){int n=Physics.OverlapCapsuleNonAlloc(p+Vector3.up*.82f,p+Vector3.up*1.62f,.55f,hits,~0,QueryTriggerInteraction.Ignore);for(int i=0;i<n;i++)if(!hits[i].transform.IsChildOf(motor.transform)){f=false;break;}}
        cells[c]=f;return f;
    }
    public static List<Vector2> Leg(Vector2 a,Vector2 b){
        var start=Vector2Int.RoundToInt(a);var target=Vector2Int.RoundToInt(b);
        Vector2Int safe=target;float best=999;
        for(int z=-3;z<=3;z++)for(int x=-3;x<=3;x++){var v=target+new Vector2Int(x,z);float d=(v-target).sqrMagnitude;if(d<best&&Free(v)){best=d;safe=v;}}
        var from=new Dictionary<Vector2Int,Vector2Int>();var costs=new Dictionary<Vector2Int,float>{{start,0}};var open=new List<Vector2Int>{start};
        while(open.Count>0){int k=0;float min=99999;for(int i=0;i<open.Count;i++){float s=costs[open[i]]+(open[i]-safe).magnitude;if(s<min){min=s;k=i;}}var c=open[k];open.RemoveAt(k);if(c==safe){var route=new List<Vector2>();while(c!=start){route.Add(c);c=from[c];}route.Reverse();return route;}
            foreach(var step in steps){var v=c+step;if(v.x<Mathf.Min(a.x,b.x)-12||v.x>Mathf.Max(a.x,b.x)+12||v.y<Mathf.Min(a.y,b.y)-12||v.y>Mathf.Max(a.y,b.y)+12||!Free(v))continue;
                if(step.x!=0&&step.y!=0&&(!Free(c+new Vector2Int(step.x,0))||!Free(c+new Vector2Int(0,step.y))))continue;
                float g=costs[c]+step.magnitude;if(costs.TryGetValue(v,out var old)&&g>=old)continue;costs[v]=g;from[v]=c;if(!open.Contains(v))open.Add(v);}
        }return new List<Vector2>{b};
    }
}
