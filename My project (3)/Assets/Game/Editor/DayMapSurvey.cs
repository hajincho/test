using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

public static class DayMapSurvey
{
    public const string Work = "C:/Users/fromj/Documents/Codex/2026-11-03/tp/work/day/";
    [MenuItem("Tools/Day Map/Survey")]
    public static void Survey()
    {
        var player=Object.FindFirstObjectByType<Game.ThirdPerson.ThirdPersonMotor>().transform.position;
        var ts=Terrain.activeTerrains;
        var s=new StringBuilder();
        s.AppendLine("spawn "+player);
        foreach (var r in GameObject.Find("Water").GetComponentsInChildren<Renderer>(true).Take(24))
            s.AppendLine("water "+r.name+" "+r.bounds);
        foreach (var id in AssetDatabase.FindAssets("t:Prefab",new[]{"Assets/TerrainDemoScene_HDRP/Prefabs/Rocks","Assets/TerrainDemoScene_HDRP/Prefabs/Trees","Assets/TerrainDemoScene_HDRP/Prefabs/Details"}))
        {
            var path=AssetDatabase.GUIDToAssetPath(id);
            var go=AssetDatabase.LoadAssetAtPath<GameObject>(path);
            var rs=go.GetComponentsInChildren<Renderer>(true);
            if(rs.Length>0)s.AppendLine(path+" "+rs[0].bounds+" colliders="+go.GetComponentsInChildren<Collider>(true).Length);
        }
        File.WriteAllText(Work+"survey.txt",s.ToString());
        using(var file=new BinaryWriter(File.Create(Work+"heights.bin")))
        for(int z=-300;z<=300;z++)
            for(int x=-300;x<=300;x++){
                var p=player+new Vector3(x,0,z);
                var t=ts.First(a=>p.x>=a.transform.position.x&&p.x<a.transform.position.x+1000&&p.z>=a.transform.position.z&&p.z<a.transform.position.z+1000);
                file.Write(t.SampleHeight(p)+t.transform.position.y);
            }
        using(var sw=new StreamWriter(Work+"edges.csv")){
        foreach(var side in new[]{0,1,2,3})
        for(int u=-1950;u<=1950;u+=10){
            var p=side==0? new Vector3(u,0,1999.99f):side==1?new Vector3(1999.99f,0,u):side==2?new Vector3(u,0,-1999.99f):new Vector3(-1999.99f,0,u);
            var t=ts.First(a=>p.x>=a.transform.position.x&&p.x<a.transform.position.x+1000&&p.z>=a.transform.position.z&&p.z<a.transform.position.z+1000);
            sw.WriteLine(side+","+u+","+(t.SampleHeight(p)+t.transform.position.y)+","+t.terrainData.GetSteepness((p.x-t.transform.position.x)/1000,(p.z-t.transform.position.z)/1000));
        }}
    }
}
