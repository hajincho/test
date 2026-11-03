using System;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;
using Game.ThirdPerson;
using Object=UnityEngine.Object;

[InitializeOnLoad]
public static class DayIslandQA
{
    static int phase,waitFrame;
    static Vector3 spawn;
    static Camera cam;
    static bool previousBackground;
    const string W="C:/Users/fromj/Documents/Codex/2026-11-03/tp/work/day/";
    static DayIslandQA(){EditorApplication.playModeStateChanged+=OnPlay;}
    [MenuItem("Tools/Day Map/Test Pine Island")]
    static void Test(){
        if(Application.isPlaying||UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)throw new Exception("Need clean Edit mode");
        SessionState.SetBool("PineIslandQA",true);EditorApplication.isPlaying=true;
    }
    static void OnPlay(PlayModeStateChange state){
        if(state==PlayModeStateChange.EnteredPlayMode && SessionState.GetBool("PineIslandQA",false)){
            phase=0;waitFrame=Time.frameCount+4;previousBackground=Application.runInBackground;Application.runInBackground=true;
            EditorApplication.update-=Update;EditorApplication.update+=Update;
        }
    }
    static void View(Vector3 offset,Vector3 aim,float fov){cam.transform.position=spawn+offset;cam.transform.LookAt(spawn+aim);cam.fieldOfView=fov;waitFrame=Time.frameCount+15;}
    static void Update(){
        if(!Application.isPlaying){EditorApplication.update-=Update;return;}
        EditorApplication.QueuePlayerLoopUpdate();if(Time.frameCount<waitFrame)return;
        try{
            if(phase==0){
                var motor=Object.FindFirstObjectByType<ThirdPersonMotor>();spawn=motor.transform.position;
                var follow=Object.FindFirstObjectByType<ThirdPersonFollowCamera>();cam=follow.GetComponent<Camera>();if(!cam)cam=Camera.main;follow.enabled=false;motor.cameraTransform=null;motor.SimulationInput=true;
                var t=GameObject.Find("Pine Island - Shore and Ridge").GetComponent<Terrain>();var root=GameObject.Find(DayIslandAuthor.RootName);
                var s=new StringBuilder();var td=t.terrainData;s.AppendLine("layers="+td.terrainLayers.Length+" splats="+td.alphamapTextureCount+" trees="+root.transform.Find("Pine grove").childCount+" scrub="+root.transform.Find("Heather and ferns").childCount+" shoreRocks="+root.transform.Find("Shore boulders").childCount);
                var hs=td.GetHeights(0,0,129,129);int land=0;foreach(float h in hs)if(t.transform.position.y+h*td.size.y> -38.08f)land++;s.AppendLine("aboveWaterSquareMetres="+(land*td.size.x*td.size.z/hs.Length));
                float len=0;var route=DayIslandAuthor.Route;
                for(int i=1;i<route.Length;i++)len+=Vector2.Distance(route[i-1],route[i]);s.AppendLine("routeMetres="+len);
                DayMapNav.Init(motor);var points=new System.Collections.Generic.List<Vector2>{Vector2.zero};
                for(int j=1;j<route.Length;j++){if(j<=8)points.AddRange(DayMapNav.Leg(points.Last(),route[j]));else points.Add(route[j]);}
                File.WriteAllLines(W+"walk-points.csv",points.Select(v=>v.x+","+v.y));
                bool ok=true;
                for(int pass=0;pass<2&&ok;pass++){
                    for(int j=1;j<points.Count;j++){
                        int i=pass==0?j:points.Count-1-j;
                        var goal=new Vector2(spawn.x,spawn.z)+points[i];
                        int ticks=0;float low=999f;
                        for(;ticks<2600;ticks++){
                            var here=motor.transform.position;var d=goal-new Vector2(here.x,here.z);if(d.magnitude<.24f)break;
                            motor.Tick(d.normalized,true,false,1f/60f);low=Mathf.Min(low,motor.transform.position.y);
                        }
                        var end=motor.transform.position;s.AppendLine("pass="+pass+" waypoint="+i+" ticks="+ticks+" pos="+end.ToString("F2")+" minY="+low.ToString("F2"));
                        if(ticks==2600){ok=false;foreach(var c in Physics.OverlapSphere(end+Vector3.up*.8f,1.8f).Take(12))s.AppendLine("near "+c.name);break;}
                    }
                }
                s.AppendLine("ROUNDTRIP="+ok);File.WriteAllText(W+"route.txt",s.ToString());
                View(new Vector3(6,20,146),new Vector3(-57,-13,184),52);
            }else if(phase==1){ScreenCapture.CaptureScreenshot(W+"island-overview.png");waitFrame=Time.frameCount+4;}
            else if(phase==2){View(new Vector3(-56.3f,-12.2f,132),new Vector3(-55,-14,185),58);}
            else if(phase==3){ScreenCapture.CaptureScreenshot(W+"bridge-view.png");waitFrame=Time.frameCount+5;}
            else {Done();return;}
            phase++;
        }catch(Exception e){File.WriteAllText(W+"qa-error.txt",e.ToString());Done();}
    }
    static void Done(){EditorApplication.update-=Update;SessionState.EraseBool("PineIslandQA");Application.runInBackground=previousBackground;EditorApplication.isPlaying=false;}
}
