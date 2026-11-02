using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.HighDefinition;

namespace Game.Environment
{
    public sealed class FireflyCompanions : MonoBehaviour
    {
        [Range(1,64)] public int count=36;
        [Range(1f,8f)] public float radius=7.5f;
        [Range(0,8)] public int lightCount=4;
        public float lightRange=16.5f;
        public float lumens=25f;
        ParticleSystem particles;
        ParticleSystem.Particle[] points;
        Light[] lamps;
        Material glow;
        float[] phase, orbit, height, pace;
        void Start()
        {
            int n=Mathf.Clamp(count,1,64);
            points=new ParticleSystem.Particle[n]; phase=new float[n]; orbit=new float[n];
            height=new float[n]; pace=new float[n]; lamps=new Light[Mathf.Clamp(lightCount,0,n)];
            var shader=Shader.Find("HDRP/Unlit");
            if(!shader) { Debug.LogWarning("Firefly shader not found."); enabled=false; return; }
            glow=new Material(shader) { name="Firefly runtime glow",enableInstancing=true };
            glow.SetColor("_UnlitColor",Color.white);
            if(glow.HasProperty("_EmissiveColor")) glow.SetColor("_EmissiveColor",new Color(2f,2f,2f,1f));
            var emitter=new GameObject("Firefly particles"); emitter.transform.SetParent(transform,false);
            particles=emitter.AddComponent<ParticleSystem>();
            var main=particles.main; main.playOnAwake=false; main.loop=false;
            main.simulationSpace=ParticleSystemSimulationSpace.Local; main.maxParticles=n;
            var emission=particles.emission; emission.enabled=false;
            var psRenderer=particles.GetComponent<ParticleSystemRenderer>();
            var sphere=GameObject.CreatePrimitive(PrimitiveType.Sphere);
            psRenderer.renderMode=ParticleSystemRenderMode.Mesh;
            psRenderer.mesh=sphere.GetComponent<MeshFilter>().sharedMesh;
            Destroy(sphere);
            psRenderer.sharedMaterial=glow;
            psRenderer.enableGPUInstancing=true;
            psRenderer.shadowCastingMode=ShadowCastingMode.Off;
            psRenderer.receiveShadows=false;
            psRenderer.motionVectorGenerationMode=MotionVectorGenerationMode.ForceNoMotion;
            particles.Play(); particles.Pause();
            for(int i=0;i<n;i++)
            {
                phase[i]=i*2.399963f;
                orbit[i]=Mathf.Lerp(1.4f,radius,Mathf.Sqrt((i+.5f)/n));
                height[i]=.4f+Mathf.Repeat(i*.731f,2.1f);
                pace[i]=.08f+Mathf.Repeat(i*.037f,.12f);
                points[i].startLifetime=1000000f; points[i].remainingLifetime=1000000f;
                points[i].startColor=Color.white;
                if(i<lamps.Length)
                {
                    var obj=new GameObject("Firefly light "+(i+1));
                    obj.transform.SetParent(transform,false);
                    var light=obj.AddComponent<Light>();
                    light.type=LightType.Point; light.range=lightRange; light.color=Color.white;
                    light.intensity=lumens; light.shadows=LightShadows.None; light.renderingLayerMask=1;
                    var hd=obj.GetComponent<HDAdditionalLightData>();
                    if(hd) { hd.affectSpecular=false; hd.volumetricDimmer=.05f; }
                    lamps[i]=light;
                }
            }
        }
        void Update()
        {
            if(!particles || points==null) return;
            float t=Time.time;
            for(int i=0;i<points.Length;i++)
            {
                float a=phase[i]+t*pace[i];
                float r=Mathf.Min(radius,orbit[i]+.25f*Mathf.Sin(t*.37f+phase[i]));
                var pos=new Vector3(Mathf.Cos(a)*r,height[i]+.22f*Mathf.Sin(t*.8f+phase[i]*1.7f),Mathf.Sin(a)*r);
                float flicker=.8f+.2f*Mathf.Sin(t*(1.1f+pace[i])+phase[i]);
                points[i].position=pos;
                points[i].startSize=(i<lamps.Length?.065f:.04f)*flicker;
                if(i<lamps.Length) { lamps[i].transform.localPosition=pos; lamps[i].intensity=lumens*(.8f+.2f*flicker); }
            }
            particles.SetParticles(points,points.Length);
        }
        void OnDestroy() { if(glow) Destroy(glow); }
    }
}