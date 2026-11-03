using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class DayIslandFinish{
    static float Dist(Vector2 p){
        var route=DayIslandAuthor.Route;float best=999;
        for(int i=9;i<route.Length-1;i++){var a=route[i];var d=route[i+1]-a;best=Mathf.Min(best,(p-a-d*Mathf.Clamp01(Vector2.Dot(p-a,d)/d.sqrMagnitude)).magnitude);}return best;
    }
    [MenuItem("Tools/Day Map/Finish Ground")]
    static void Finish(){
        var t=GameObject.Find("Pine Island - Shore and Ridge").GetComponent<Terrain>();var td=t.terrainData;
        var source=Terrain.activeTerrains.First(a=>a!=t&&a.terrainData.detailPrototypes.Length>0);
        var origin=new Vector2(-99,155);float[,] hs=td.GetHeights(0,0,129,129);
        var route=DayIslandAuthor.Route;
        // Give the dock a graded approach and ease the climb around the wooded saddle.
        float[] ys={-35.64f,-35.12f,-33.49f,-32.52f,-31.67f,-29.98f,-29.04f};
        for(int z=0;z<129;z++)for(int x=0;x<129;x++){
            var p=origin+new Vector2(x*86/128f,z*78/128f);
            float best=99,grade=0;
            for(int i=9;i<15;i++){var d=route[i+1]-route[i];float f=Mathf.Clamp01(Vector2.Dot(p-route[i],d)/d.sqrMagnitude);float distance=(p-route[i]-d*f).magnitude;
                if(distance<best){best=distance;grade=Mathf.Lerp(ys[i-9],ys[i-8],f);}}
            float blend=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(1.7f,5.8f,best));
            if(p.y<170)blend*=Mathf.SmoothStep(0,1,Mathf.InverseLerp(167,170,p.y));
            hs[z,x]=Mathf.Lerp(hs[z,x],(grade+42f)/16f,blend);
        }
        td.SetHeights(0,0,hs);
        var alpha=new float[128,128,4];var grass=new int[128,128];var tuft=new int[128,128];var fern=new int[128,128];
        for(int z=0;z<128;z++)for(int x=0;x<128;x++){
            float u=(x+.5f)/128,v=(z+.5f)/128;var p=origin+new Vector2(86*u,78*v);
            float h=-42+4f*(hs[z,x]+hs[z+1,x]+hs[z,x+1]+hs[z+1,x+1]);float n=Mathf.PerlinNoise(u*15+4,v*15+9);
            float shore=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(-37.1f,-35.5f,h+.5f*n));
            float path=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(1f,2.15f,Dist(p)+.45f*(n-.5f)));
            float stone=(1-shore)*(1-path)*Mathf.InverseLerp(25,43,td.GetSteepness(u,v))*.65f;
            float soil=(1-shore-stone)*Mathf.Lerp(.06f+.20f*n,.98f,path);
            alpha[z,x,0]=shore;alpha[z,x,1]=soil;alpha[z,x,2]=1-shore-stone-soil;alpha[z,x,3]=stone;
            float meadow=(1-shore)*(1-path)*(1-stone);
            grass[z,x]=Mathf.RoundToInt(meadow*(4+6*n));tuft[z,x]=Mathf.RoundToInt(meadow*Mathf.InverseLerp(.38f,.78f,n)*4);
            fern[z,x]=Mathf.RoundToInt(meadow*Mathf.InverseLerp(.63f,.8f,n)*2);
        }
        td.SetAlphamaps(0,0,alpha);
        td.SetDetailResolution(128,16);td.detailPrototypes=new[]{"Grass_A","Grass_B","Fern_A"}.Select(n=>source.terrainData.detailPrototypes.First(d=>d.prototype&&d.prototype.name==n)).ToArray();td.SetDetailLayer(0,0,0,grass);td.SetDetailLayer(0,0,1,tuft);td.SetDetailLayer(0,0,2,fern);
        t.detailObjectDensity=.8f;t.detailObjectDistance=100;
        foreach(var a in td.alphamapTextures){EditorUtility.SetDirty(a);AssetDatabase.SaveAssetIfDirty(a);}
        EditorUtility.SetDirty(td);AssetDatabase.SaveAssetIfDirty(td);t.Flush();
        // Seat and flanking rocks follow the final sculpt.
        var from=UnityEngine.Object.FindFirstObjectByType<Game.ThirdPerson.ThirdPersonMotor>().transform.position;
        var seat=GameObject.Find("Lakeside bench").transform;var pt=seat.position;pt.y=t.SampleHeight(pt)+t.transform.position.y;seat.position=pt;
        EditorSceneManager.MarkSceneDirty(t.gameObject.scene);EditorSceneManager.SaveScene(t.gameObject.scene);
        var test=td.GetAlphamaps(63,63,1,1);File.WriteAllText(DayMapSurvey.Work+"paint.txt","grass="+test[0,0,2]+" path="+test[0,0,1]+" detail types="+td.detailPrototypes.Length);
    }
}
