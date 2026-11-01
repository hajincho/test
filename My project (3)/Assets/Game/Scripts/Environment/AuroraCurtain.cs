using UnityEngine;

namespace Game.Environment
{
    [ExecuteAlways, RequireComponent(typeof(MeshFilter), typeof(MeshRenderer))]
    public class AuroraCurtain : MonoBehaviour
    {
        public float startYaw = 30f;
        public float endYaw = 88f;
        public float radius = 3500f;
        public float speed = 0.14f;
        public float seed = 0f;
        public float baseElevation = 20f;
        public float verticalSpan = 28f;
        public float opacity = 0.16f;
        public float animationSpeedMultiplier = 2f;
        public float motionAmplitude = 2f;
        const int Columns = 64;
        const int Rows = 16;
        Mesh mesh;
        Vector3[] vertices;
        MaterialPropertyBlock properties;
        Texture2D veil;
        Color[] colorBuffer;
        Color[] displayBuffer;
        float lastDisplayTime = float.NegativeInfinity;
        MeshRenderer cachedRenderer;
        float lastUpdateTime = float.NegativeInfinity;
        float lastTextureTime = float.NegativeInfinity;

        void OnEnable() { Build(); Evaluate(0); }
        void Build()
        {
            if (mesh != null && vertices != null && vertices.Length == (Columns + 1) * (Rows + 1) && veil != null && properties != null && colorBuffer != null && colorBuffer.Length == 128 * 64 && cachedRenderer != null && displayBuffer != null) return; if (mesh != null) { if (Application.isPlaying) Destroy(mesh); else DestroyImmediate(mesh); } if (veil != null) { if (Application.isPlaying) Destroy(veil); else DestroyImmediate(veil); }
            mesh = new Mesh { name = "Animated Aurora Curtain", hideFlags = HideFlags.DontSave };
            vertices = new Vector3[(Columns + 1) * (Rows + 1)];
            var uv = new Vector2[vertices.Length];
            var triangles = new int[Columns * Rows * 6];
            int t = 0;
            for (int x = 0; x <= Columns; x++) for (int y = 0; y <= Rows; y++)
            {
                int i = x * (Rows + 1) + y;
                uv[i] = new Vector2(x / (float)Columns, y / (float)Rows);
                if (x == Columns || y == Rows) continue;
                triangles[t++] = i; triangles[t++] = i + 1; triangles[t++] = i + Rows + 1;
                triangles[t++] = i + 1; triangles[t++] = i + Rows + 2; triangles[t++] = i + Rows + 1;
            }
            mesh.vertices = vertices; mesh.uv = uv; mesh.triangles = triangles;
            GetComponent<MeshFilter>().sharedMesh = mesh;
            properties = new MaterialPropertyBlock();
            veil = new Texture2D(128, 64, TextureFormat.RGBAHalf, true, true) { name = "Soft Living Aurora", wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Trilinear, anisoLevel = 2, hideFlags = HideFlags.DontSave };
            colorBuffer = new Color[128 * 64]; displayBuffer = new Color[128 * 64]; lastDisplayTime = float.NegativeInfinity; cachedRenderer = GetComponent<MeshRenderer>(); mesh.MarkDynamic(); lastTextureTime = float.NegativeInfinity;
        }
        void Update()
        {
            float now = (float)Time.realtimeSinceStartupAsDouble;
            var camera = Camera.main;
            if (camera != null)
            {
                transform.position = camera.transform.position;
                float middle = (startYaw + endYaw) * .5f;
                if (Mathf.Abs(Mathf.DeltaAngle(camera.transform.eulerAngles.y, middle)) > (endYaw - startYaw) * .5f + 75f) return;
            }
            if (now - lastUpdateTime < .05f) return;
            lastUpdateTime = now;
            Evaluate(now);
        }
        public void Evaluate(float seconds)
        {
            Build();
            float animationSeconds = seconds * animationSpeedMultiplier;
            float time = animationSeconds * speed + seed;
            var camera = Camera.main;
            if (camera != null) transform.position = camera.transform.position;
            for (int x = 0; x <= Columns; x++)
            {
                float u = x / (float)Columns;
                float yaw = Mathf.Lerp(startYaw, endYaw, u) + (Mathf.PerlinNoise(u * 5f, time * .13f + 10f) - .5f) * .3f * motionAmplitude;
                float bottom = baseElevation + 4.5f + (Mathf.PerlinNoise(Mathf.Lerp(startYaw, endYaw, u) * .035f + 10f, animationSeconds * .012f) - .5f) * 9f * motionAmplitude;
                for (int y = 0; y <= Rows; y++)
                {
                    float v = y / (float)Rows;
                    float top = Mathf.Min(82f, bottom + verticalSpan + 3f + (Mathf.PerlinNoise(Mathf.Lerp(startYaw, endYaw, u) * .045f, animationSeconds * .02f + 20f) - .5f) * 6f * motionAmplitude);
                    float elevation = Mathf.Lerp(bottom, top, v) * Mathf.Deg2Rad;
                    float angle = yaw * Mathf.Deg2Rad;
                    vertices[x * (Rows + 1) + y] = new Vector3(Mathf.Sin(angle) * Mathf.Cos(elevation), Mathf.Sin(elevation), Mathf.Cos(angle) * Mathf.Cos(elevation)) * radius;
                }
            }
            mesh.vertices = vertices; mesh.bounds = new Bounds(Vector3.zero, Vector3.one * radius * 2.1f);
            if (Mathf.Abs(seconds - lastTextureTime) > .2f)
            {
                var colors = colorBuffer;
                for (int x = 0; x < 128; x++)
                {
                    float u = x / 127f;
                    float horizontal = Mathf.Lerp(startYaw, endYaw, u) * .018f;
                    float broad = Mathf.PerlinNoise(horizontal * 2.1f, animationSeconds * .025f + 20f);
                    float fold = Mathf.PerlinNoise(horizontal * 11f + broad, time * .04f + 50f);
                    float curve = .62f + (Mathf.Sin(horizontal * 2.1f + animationSeconds * .018f) * .17f + (broad - .5f) * .2f) * motionAmplitude;
                    for (int y = 0; y < 64; y++)
                    {
                    float v = y / 63f;
                    float offset = v - curve;
                    float core = Mathf.Exp(-Mathf.Pow(offset / (.07f + fold * .055f), 2f));
                    float halo = Mathf.Exp(-Mathf.Pow(offset / .19f, 2f));
                    float fibre = Mathf.PerlinNoise(horizontal * 23f + fold * .7f, v * .45f - time * .12f + 10f);
                    float pulse = Mathf.PerlinNoise(horizontal * 21f, v * 5f - animationSeconds * .16f + 70f);
                    float rays = Mathf.Exp(Mathf.Min(offset, 0f) / .30f) * Mathf.Pow(Mathf.Clamp01(fibre), 1.4f) * (.45f + pulse * .8f) * (1f - Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(-.04f, .04f, offset)));
                    float secondary = Mathf.Exp(-Mathf.Pow((v - curve + .25f + broad * .13f) / .065f, 2f)) * .2f;
                    float edgeLeft = Mathf.SmoothStep(0, 1, Mathf.Clamp01(u / .20f));
                    float edgeRight = Mathf.SmoothStep(0, 1, Mathf.Clamp01((1-u) / .20f));
                    float edges = edgeLeft * edgeRight * Mathf.SmoothStep(0, 1, Mathf.Clamp01(v * 4f)) * Mathf.SmoothStep(0, 1, Mathf.Clamp01((1-v) * 4f));
                    float alpha = (core * .48f + halo * .3f + rays * .55f + secondary) * edges * opacity;
                    Color teal = new Color(.035f, .85f, .66f);
                    Color blue = new Color(.025f, .28f, .68f);
                    Color color = Color.Lerp(blue, teal, Mathf.Clamp01(core * .8f + halo * .35f + fibre * .25f));
                    color = Color.Lerp(color, new Color(.27f, .18f, .56f), Mathf.Clamp01(offset * 2f) * .35f);
                    color.a = float.IsNaN(alpha) || float.IsInfinity(alpha) ? 0f : Mathf.Clamp01(alpha);
                    colors[x + 128 * y] = color;
                    }
                }
                
                lastTextureTime = seconds;
            }
            float blend = float.IsNegativeInfinity(lastDisplayTime) ? 1f : 1f - Mathf.Exp(-Mathf.Abs(seconds - lastDisplayTime) * 10f);
            for (int y = 0; y < 64; y++) for (int x = 0; x < 128; x++)
            {
                int i = x + y * 128;
                Color softened = (colorBuffer[i] * 2f + colorBuffer[Mathf.Max(0,x-1)+y*128] + colorBuffer[Mathf.Min(127,x+1)+y*128] + colorBuffer[x+Mathf.Max(0,y-1)*128] + colorBuffer[x+Mathf.Min(63,y+1)*128]) / 6f;
                if (float.IsNaN(softened.a) || float.IsInfinity(softened.a)) softened = Color.clear;
                if (float.IsNaN(displayBuffer[i].a) || float.IsInfinity(displayBuffer[i].a)) displayBuffer[i] = softened;
                displayBuffer[i] = Color.Lerp(displayBuffer[i], softened, blend);
            }
            veil.SetPixels(displayBuffer); veil.Apply(true, false);
            lastDisplayTime = seconds;
            properties.SetTexture("_UnlitColorMap", veil);
            properties.SetVector("_UnlitColorMap_ST", new Vector4(1, 1, 0, 0));
            cachedRenderer.SetPropertyBlock(properties);
        }
        void OnDestroy()
        {
            if (mesh == null) return;
            if (Application.isPlaying) Destroy(mesh); else DestroyImmediate(mesh);
        }
    }
}
