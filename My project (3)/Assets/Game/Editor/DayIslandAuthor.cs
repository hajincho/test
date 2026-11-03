using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class DayIslandAuthor
{
    public const string Folder="Assets/Game/Environment/PineIsland";
    const string Pack="Assets/TerrainDemoScene_HDRP/";
    const string Day="Assets/TerrainDemoScene_HDRP/Scenes/TerrainOriginal_Day.unity";
    public const string RootName="Pine Island - Day";
    public static readonly Vector2[] Route={new Vector2(0,0), new Vector2(-7,14),new Vector2(-19,36),new Vector2(-24,60),new Vector2(-34,81),new Vector2(-43,102),new Vector2(-50,117),new Vector2(-55,130),new Vector2(-55,136),new Vector2(-55,170),new Vector2(-55,176),new Vector2(-64,184),new Vector2(-67,191),new Vector2(-62,199),new Vector2(-48,205),new Vector2(-39,206)};
    public static Vector3 Spawn;
    static Terrain[] mainland;
    static Terrain island;
    static Transform root;
    static Material wood,metal,sign;
    static Mesh signMesh,seatMesh;
    static System.Random rand;
    static float Range(float a,float b)=>Mathf.Lerp(a,b,(float)rand.NextDouble());
    public static Vector3 World(Vector2 p)=>new Vector3(Spawn.x+p.x,0,Spawn.z+p.y);
    static float Old(Vector2 p){
        var v=World(p);var t=mainland.First(a=>v.x>=a.transform.position.x&&v.x<a.transform.position.x+a.terrainData.size.x&&v.z>=a.transform.position.z&&v.z<a.transform.position.z+a.terrainData.size.z);
        return t.transform.position.y+t.SampleHeight(v);
    }
    static float Ground(Vector2 p){
        float h=Old(p); var v=World(p);
        if(island){var local=v-island.transform.position; if(local.x>=0&&local.z>=0&&local.x<=86&&local.z<=78)h=Mathf.Max(h,island.transform.position.y+island.SampleHeight(v));}return h;
    }
    static float PathDistance(Vector2 p,int start,int end){
        float best=float.PositiveInfinity;
        for(int i=start;i<end;i++){var a=Route[i];var d=Route[i+1]-a;best=Mathf.Min(best,(p-a-d*Mathf.Clamp01(Vector2.Dot(p-a,d)/d.sqrMagnitude)).magnitude);}return best;
    }
    static Transform Group(string name,Transform parent){var go=new GameObject(name);go.transform.SetParent(parent,false);return go.transform;}
    static Material Mat(string name,string texture,Color color,float smooth,float metallic=0){
        var m=new Material(Shader.Find("HDRP/Lit"));m.name=name;m.SetColor("_BaseColor",color);m.SetFloat("_Smoothness",smooth);m.SetFloat("_Metallic",metallic);
        if(texture!=null)m.SetTexture("_BaseColorMap",AssetDatabase.LoadAssetAtPath<Texture2D>(Folder+"/"+texture+".png"));
        AssetDatabase.CreateAsset(m,Folder+"/"+name+".mat");return m;
    }
    static void BuildIsland(){
        var td=new TerrainData();td.name="Pine Island";td.heightmapResolution=129;td.size=new Vector3(86,16,78);td.alphamapResolution=128;td.baseMapResolution=256;td.SetDetailResolution(0,8);
        string[] layers={"Pebbles_B","Grass_Soil_A","Grass_Moss_A","Cliff_Mossy_E"};
        td.terrainLayers=layers.Select(l=>AssetDatabase.LoadAssetAtPath<TerrainLayer>(Pack+"Terrain/Layers/"+l+".terrainlayer")).ToArray();
        if(td.terrainLayers.Any(l=>!l))throw new Exception("Missing island ground layer");
        var heights=new float[129,129];var land=new Vector2(-56,194);var origin=land-new Vector2(43,39);
        float landing=Old(Route[8]);
        for(int z=0;z<129;z++)for(int x=0;x<129;x++){
            var p=origin+new Vector2(x*86/128f,z*78/128f);var q=p-land;
            float a=Mathf.Atan2(q.y/31,q.x/36),r=new Vector2(q.x/36,q.y/31).magnitude/(1+.075f*Mathf.Sin(3*a+.3f)+.048f*Mathf.Cos(5*a-.6f));
            float inside=Mathf.SmoothStep(0,1,Mathf.InverseLerp(1.12f,.42f,r));
            float noise=Mathf.PerlinNoise(x*.055f+64,z*.055f+11)-.5f;
            float hill=4.3f*Mathf.Exp(-((q.x-16)*(q.x-16)/175+(q.y-10)*(q.y-10)/135));
            float y=-41.15f+inside*(9.4f+hill)+noise*(inside*.85f+.35f);
            float dock=Mathf.SmoothStep(0,1,Mathf.InverseLerp(8,2,Mathf.Abs(p.x+55)))*Mathf.SmoothStep(0,1,Mathf.InverseLerp(161,169,p.y))*(1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(173,181,p.y)));
            y=Mathf.Lerp(y,landing+.06f*(p.y-170),dock);
            heights[z,x]=Mathf.InverseLerp(-42,-26,y);
        }
        td.SetHeights(0,0,heights);var alpha=new float[128,128,4];
        for(int z=0;z<128;z++)for(int x=0;x<128;x++){
            float u=(x+.5f)/128,v=(z+.5f)/128;var p=origin+new Vector2(86*u,78*v);float y=-42+td.GetInterpolatedHeight(u,v);
            float noise=Mathf.PerlinNoise(u*15+4,v*15+9);
            float beach=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(-37.6f,-35.4f,y+noise*.6f));
            float path=1-Mathf.SmoothStep(0,1,Mathf.InverseLerp(.9f,2.4f,PathDistance(p,9,15)+.6f*(noise-.5f)));
            float rock=(1-beach)*(1-path)*Mathf.InverseLerp(20,42,td.GetSteepness(u,v))*.85f;
            float soil=(1-beach-rock)*Mathf.Lerp(noise*.35f,.93f,path);
            alpha[z,x,0]=beach;alpha[z,x,1]=soil;alpha[z,x,2]=1-beach-rock-soil;alpha[z,x,3]=rock;
        }
        td.SetAlphamaps(0,0,alpha);AssetDatabase.CreateAsset(td,Folder+"/PineIslandTerrain.asset");
        var go=Terrain.CreateTerrainGameObject(td);go.name="Pine Island - Shore and Ridge";go.transform.SetParent(root,false);go.transform.position=World(origin)+Vector3.down*42;
        island=go.GetComponent<Terrain>();island.allowAutoConnect=false;island.groupingID=901;island.materialTemplate=mainland[0].materialTemplate;island.heightmapPixelError=3;island.drawInstanced=true;
    }
    sealed class TimberMesh{
        readonly List<Vector3> vs=new List<Vector3>();readonly List<Vector2> uv=new List<Vector2>();readonly List<int>[] ts={new List<int>(),new List<int>(),new List<int>()};
        public void Face(Vector3 a,Vector3 b,Vector3 c,Vector3 d,int slot){
            int n=vs.Count;vs.AddRange(new[]{a,b,c,d});float off=(n%117)*.047f;
            float l=(b-a).magnitude,w=(d-a).magnitude;
            if(slot==2)uv.AddRange(new[]{new Vector2(0,0),new Vector2(0,1),new Vector2(1,1),new Vector2(1,0)});
            else {var first=l>w?new Vector2(l*.42f,0):new Vector2(0,l*.8f);var second=l>w?new Vector2(0,w*.8f):new Vector2(w*.42f,0);var o=new Vector2(off,.3f*off);uv.AddRange(new[]{o,o+first,o+first+second,o+second});}
            ts[slot].AddRange(new[]{n,n+1,n+2,n,n+2,n+3});
        }
        public void Box(Vector3 pos,Vector3 size,int slot=0,Quaternion? rotation=null){
            var rot=rotation??Quaternion.identity;var v=new Vector3[8]; for(int i=0;i<8;i++)v[i]=pos+rot*Vector3.Scale(size,new Vector3((i&1)==0?-.5f:.5f,(i&2)==0?-.5f:.5f,(i&4)==0?-.5f:.5f));
            Face(v[0],v[2],v[3],v[1],slot);Face(v[4],v[5],v[7],v[6],slot);Face(v[0],v[4],v[6],v[2],slot);Face(v[1],v[3],v[7],v[5],slot);Face(v[2],v[6],v[7],v[3],slot);Face(v[0],v[1],v[5],v[4],slot);
        }
        public void Beam(Vector3 a,Vector3 b,float width,float height,int slot=0){var d=b-a;Box((a+b)*.5f,new Vector3(width,height,d.magnitude),slot,Quaternion.FromToRotation(Vector3.forward,d));}
        public Mesh Save(string name){var m=new Mesh{name=name};m.SetVertices(vs);m.SetUVs(0,uv);m.subMeshCount=ts[2].Count>0?3:2;for(int i=0;i<m.subMeshCount;i++)m.SetTriangles(ts[i],i);m.RecalculateNormals();m.RecalculateTangents();m.RecalculateBounds();AssetDatabase.CreateAsset(m,Folder+"/"+name+".asset");return m;}
    }
    static GameObject PlaceMesh(string name,Mesh mesh,Vector3 p,Quaternion rot,Transform group){
        var go=new GameObject(name);go.transform.SetParent(group,false);go.transform.SetPositionAndRotation(p,rot);go.AddComponent<MeshFilter>().sharedMesh=mesh;go.AddComponent<MeshRenderer>().sharedMaterials=mesh.subMeshCount==3?new[]{wood,metal,sign}:new[]{wood,metal};return go;
    }
    static void Collider(GameObject go,Vector3 c,Vector3 size){var b=go.AddComponent<BoxCollider>();b.center=c;b.size=size;}
    static void BuildBridge(Transform group){
        Vector3 start=World(Route[8])+Vector3.up*(Ground(Route[8])+.025f),end=World(Route[9])+Vector3.up*(Ground(Route[9])+.025f);
        float len=(end-start).magnitude;var mesh=new TimberMesh();int planks=Mathf.CeilToInt(len/.29f);
        for(int i=0;i<planks;i++){float z=(i+.5f)*len/planks;mesh.Box(new Vector3(0,-.08f,z),new Vector3(2.75f+Range(-.055f,.055f),.16f,len/planks-.013f));}
        for(int side=-1;side<=1;side+=2){
            mesh.Box(new Vector3(side*.91f,-.27f,len/2),new Vector3(.22f,.29f,len));
            int spans=9;
            for(int i=0;i<=spans;i++){
                float z=i*len/spans;mesh.Box(new Vector3(side*1.37f,-1.87f,z),new Vector3(.21f,5.8f,.22f));mesh.Box(new Vector3(side*1.37f,.81f,z),new Vector3(.225f,.065f,.235f),1);
                if(i==spans)continue;
                float next=(i+1)*len/spans;
                mesh.Beam(new Vector3(side*1.37f,.98f,z),new Vector3(side*1.37f,.98f,next),.13f,.12f);
                mesh.Beam(new Vector3(side*1.37f,.43f,z),new Vector3(side*1.37f,.43f,next),.085f,.095f);
                mesh.Beam(new Vector3(side*1.37f,-1.58f,z),new Vector3(side*1.37f,-.3f,next),.14f,.18f);
            }
        }
        var bridge=PlaceMesh("Larch footbridge",mesh.Save("LarchFootbridge"),start,Quaternion.LookRotation(end-start),group);
        Collider(bridge,new Vector3(0,-.1f,len/2),new Vector3(2.76f,.2f,len));for(int s=-1;s<=1;s+=2)Collider(bridge,new Vector3(s*1.37f,.50f,len/2),new Vector3(.15f,1f,len));
    }
    static void BuildFurniture(Transform group){
        var m=new TimberMesh();m.Box(new Vector3(0,.76f,0),new Vector3(.135f,1.62f,.135f));m.Box(new Vector3(0,1.48f,-.085f),new Vector3(1.03f,.39f,.09f));m.Face(new Vector3(-.49f,1.32f,-.132f),new Vector3(-.49f,1.64f,-.132f),new Vector3(.49f,1.64f,-.132f),new Vector3(.49f,1.32f,-.132f),2);
        m.Box(new Vector3(0,.89f,0),new Vector3(.145f,.045f,.145f),1);signMesh=m.Save("TrailWaymark");
        foreach(int i in new[]{1,4,8}){var dir=(Route[i+1]-Route[i]).normalized;var p=Route[i]+new Vector2(dir.y,-dir.x)*2.35f;var go=PlaceMesh("Pine Island waymark",signMesh,World(p)+Vector3.up*(Ground(p)-.025f),Quaternion.LookRotation(new Vector3(dir.x,0,dir.y)),group);Collider(go,new Vector3(0,.75f,0),new Vector3(.14f,1.5f,.14f));}
        m=new TimberMesh();for(int i=-1;i<=1;i++)m.Box(new Vector3(0,.46f,i*.165f),new Vector3(2.15f,.095f,.15f));
        foreach(int i in new[]{-1,1}){m.Box(new Vector3(i*.77f,.19f,0),new Vector3(.25f,.44f,.4f));m.Box(new Vector3(i*.77f,.45f,0),new Vector3(.05f,.14f,.47f),1);}
        seatMesh=m.Save("LookoutBench");var pos=new Vector2(-39,209);var bench=PlaceMesh("Lakeside bench",seatMesh,World(pos)+Vector3.up*Ground(pos),Quaternion.Euler(0,-20,0),group);Collider(bench,new Vector3(0,.25f,0),new Vector3(2.15f,.5f,.48f));
    }
    static GameObject Prop(string relative, Vector2 p,float scale,float yaw,Transform group,float sink=0){
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(Pack+"Prefabs/"+relative+".prefab");if(!prefab)throw new Exception(relative);
        var go=(GameObject)PrefabUtility.InstantiatePrefab(prefab,group.gameObject.scene);go.transform.SetParent(group,false);go.transform.SetPositionAndRotation(World(p)+Vector3.up*(Ground(p)-sink),Quaternion.Euler(0,yaw,0));go.transform.localScale=Vector3.one*scale;
        PrefabUtility.RecordPrefabInstancePropertyModifications(go.transform);return go;
    }
    static void Plant(){
        var grove=Group("Pine grove",root);var margins=Group("Heather and ferns",root);var rocks=Group("Shore boulders",root);
        var trees=new List<Vector2>();
        for(int i=0;i<500&&trees.Count<19;i++){
            var p=new Vector2(Range(-88,-24),Range(169,218));
            if(Ground(p)<-35||PathDistance(p,8,15)<5||trees.Any(t=>(t-p).magnitude<4.8f)||(p-new Vector2(-39,208)).magnitude<9)continue;
            var letter="ABCD"[trees.Count%4];Prop("Trees/Pines/Pine_"+letter+"/Pine_"+letter,p,Range(.38f,.78f),Range(0,360),grove,.13f);trees.Add(p);
        }
        string[] scrub={"Heather_A","Fern_B","Heather_B","Grass_A","Bush_B"};
        for(int i=0;i<120;i++){var p=new Vector2(Range(-92,-22),Range(166,223));float h=Ground(p);if(h<-36.8f||PathDistance(p,8,15)<1.9f)continue;Prop("Details/"+scrub[i%5],p,Range(.75f,1.5f),Range(0,360),margins,.04f);}
        for(int i=0;i<90;i++){var p=new Vector2(Range(-96,-14),Range(159,226));float h=Ground(p);if(h<-39.6f||h>-34.8f||PathDistance(p,8,15)<3.5f)continue;var style=i%3==0?"Rock_Overgrown_D":"Rock_Overgrown_C";Prop("Rocks/"+style,p,Range(.38f,.98f),Range(0,360),rocks,Range(.2f,.55f));}
        var path=Group("Mainland trail markers",root);
        for(int i=1;i<8;i++){var d=(Route[i+1]-Route[i]).normalized; var p=Route[i]+new Vector2(-d.y,d.x)*(i%2==0?3.2f:-3.2f);Prop("Rocks/Rock_C_02",p,.38f,Range(0,360),path,.15f);Prop("Details/Heather_B",p+new Vector2(.75f,.62f),1.2f,Range(0,360),path);}
        var lookout=Group("Rock lookout",root);Prop("Rocks/Rock_Overgrown_C",new Vector2(-34,208),.63f,35,lookout,.46f);Prop("Rocks/Rock_Overgrown_D",new Vector2(-38,214),.81f,-16,lookout,.42f);
    }
    [MenuItem("Tools/Day Map/Build Pine Island")]
    public static void Build(){
        var sc=SceneManager.GetActiveScene();if(Application.isPlaying||sc.path!=Day||sc.isDirty||GameObject.Find(RootName))throw new Exception("Expected clean day scene without expansion");
        if(AssetDatabase.LoadAssetAtPath<TerrainData>(Folder+"/PineIslandTerrain.asset"))throw new Exception("Island already exists");
        mainland=Terrain.activeTerrains;Spawn=UnityEngine.Object.FindFirstObjectByType<Game.ThirdPerson.ThirdPersonMotor>().transform.position;rand=new System.Random(52301);
        root=Group(RootName,null);wood=Mat("WeatheredLarch","LarchGrain",Color.white,.19f);metal=Mat("ForgedIron",null,new Color(.15f,.14f,.12f),.35f,.55f);sign=Mat("PaintedWaymark","PineIslandWaymark",Color.white,.25f);
        BuildIsland();var group=Group("Bridge and waymarks",root);BuildBridge(group);BuildFurniture(group);Plant();
        EditorSceneManager.MarkSceneDirty(sc);if(!EditorSceneManager.SaveScene(sc))throw new Exception("Could not save day scene");
        File.WriteAllText(DayMapSurvey.Work+"built.txt","island centre "+World(new Vector2(-56,194))+"; objects="+root.GetComponentsInChildren<Transform>(true).Length+"; bridgeLength="+(Route[9]-Route[8]).magnitude);
    }
}
