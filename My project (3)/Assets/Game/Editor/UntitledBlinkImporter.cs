using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

namespace Game.ThirdPerson.Editor
{
    // The source rig has separate skin, eye outline, lash and iris meshes.
    // Derive one synchronized shape at import time so every instance can use normal skinning.
    sealed class UntitledBlinkImporter : AssetPostprocessor
    {
        const string Model = "Assets/Game/Characters/Untitled/UntitledCharacter.fbx";
        public override uint GetVersion() => 1;

        void OnPostprocessModel(GameObject root)
        {
            if (assetPath != Model) return;
            var parts = root.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            var outline = System.Array.Find(parts, r => r.name == "CharacterMesh_18");
            if (!outline) return;
            var frame = root.transform.worldToLocalMatrix * outline.localToWorldMatrix;
            var rim = new List<Vector2>();
            foreach (var vertex in outline.sharedMesh.vertices)
            {
                Vector3 p = frame.MultiplyPoint3x4(vertex);
                if (p.x > 0f) rim.Add(new Vector2(p.x, p.y));
            }
            if (rim.Count < 3) return;
            // The outline is a thin ring with split vertices. Its convex silhouette
            // supplies both lid heights at each horizontal slice of the eye.
            var hull = ConvexHull(rim);
            foreach (var part in parts)
            {
                bool skin = part.name == "CharacterMesh_15" || part.name == "CharacterMesh_17";
                bool lash = part.name == "CharacterMesh_20";
                bool iris = part.name == "CharacterMesh_00" || part.name == "CharacterMesh_21";
                if (!skin && !lash && !iris && part != outline) continue;
                var mesh = part.sharedMesh;
                if (mesh.GetBlendShapeIndex("IdleBlink") >= 0) continue;
                var toBody = root.transform.worldToLocalMatrix * part.localToWorldMatrix;
                var toMesh = toBody.inverse;
                var vertices = mesh.vertices;
                var deltas = new Vector3[vertices.Length];
                for (int i = 0; i < vertices.Length; i++)
                {
                    Vector3 p = toBody.MultiplyPoint3x4(vertices[i]);
                    Vector3 closed = CloseLids(p, hull, iris, lash);
                    deltas[i] = toMesh.MultiplyVector(closed - p);
                }
                mesh.AddBlendShapeFrame("IdleBlink", 100f, deltas, null, null);
            }
        }

        static List<Vector2> ConvexHull(List<Vector2> points)
        {
            points.Sort((p,q) => p.x != q.x ? p.x.CompareTo(q.x) : p.y.CompareTo(q.y));
            var hull = new List<Vector2>();
            for (int pass = 0; pass < 2; pass++)
            {
                int start = hull.Count;
                for (int j=0; j<points.Count; j++)
                {
                    Vector2 p = points[pass == 0 ? j : points.Count-1-j];
                    while (hull.Count >= start+2)
                    {
                        Vector2 a=hull[hull.Count-2], b=hull[hull.Count-1];
                        if ((b.x-a.x)*(p.y-a.y) - (b.y-a.y)*(p.x-a.x) > 0f) break;
                        hull.RemoveAt(hull.Count-1);
                    }
                    hull.Add(p);
                }
                hull.RemoveAt(hull.Count-1);
            }
            return hull;
        }

        static Vector3 CloseLids(Vector3 p, List<Vector2> hull, bool iris, bool lash)
        {
            if (iris) { p.z -= .012f; return p; }
            float x = Mathf.Abs(p.x);
            if (x < .012f || x > .074f || p.y < 1.373f || p.y > 1.443f || p.z < .065f) return p;
            float slice = Mathf.Clamp(x, hull[0].x + .00001f, .0601f);
            float low = float.PositiveInfinity, high = float.NegativeInfinity;
            for (int j=0; j<hull.Count; j++)
            {
                Vector2 a=hull[j], b=hull[(j+1)%hull.Count];
                if ((slice-a.x)*(slice-b.x)>0f || Mathf.Abs(b.x-a.x)<.0000001f) continue;
                float y = Mathf.Lerp(a.y,b.y,(slice-a.x)/(b.x-a.x));
                low=Mathf.Min(low,y); high=Mathf.Max(high,y);
            }
            if (float.IsInfinity(low)) return p;
            float t = Mathf.Clamp01((x-.024f)/.036f);
            float seam = Mathf.Lerp(1.4053f,1.4108f,t)-.0092f*4f*t*(1f-t);
            float surface = Mathf.Lerp(.098f,.087f,t)+.004f*4f*t*(1f-t);
            if (lash)
            {
                p.y=seam+.0005f+(p.y-high)*.28f;
                p.z=Mathf.Max(p.z,surface+.0022f);
                return p;
            }
            float side = Mathf.InverseLerp(.013f,.024f,x)*(1f-Mathf.InverseLerp(.0602f,.073f,x));
            float outside = Mathf.Max(low-p.y,p.y-high,0f);
            float w=side*(1f-Mathf.SmoothStep(0f,1f,Mathf.InverseLerp(.001f,.020f,outside)));
            float rimY = Mathf.Clamp(p.y,low,high);
            float lip = Mathf.Lerp(.00045f,-.00045f,Mathf.InverseLerp(low,high,rimY));
            p.y += (seam+lip-rimY)*w;
            p.z = Mathf.Lerp(p.z,surface,w);
            return p;
        }
    }
}
