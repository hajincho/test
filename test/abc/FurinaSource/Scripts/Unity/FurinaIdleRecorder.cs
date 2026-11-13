// Reference copy. Put in "My project urp/Assets/Game/Editor/", then run:
//   Unity.exe -batchmode -projectPath "<My project urp>" -executeMethod FurinaIdleRecorder.Run -logFile <log>
// It plays Assets/Scenes/Demo.unity headless, waits 4 s, records Furina's 55 body joints for 10.5 s at 30 fps
// into OutPath and exits. Delete it from the Unity project afterwards.
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class FurinaIdleRecorder
{
    const string Flag = "FurinaIdleRecorder.run";
    const string OutPath = @"C:\Users\fromj\Downloads\test\test\abc\FurinaSource\Data\unity_idle.json";
    const int SettleFrames = 120, RecordFrames = 315; // 30 fps: 4 s settle, 10.5 s (three breaths)

    static readonly string[] Body = {
        "Hips", "Spine", "Chest", "Neck", "Head",
        "Left shoulder", "Left arm", "zArmTwist_L", "Left elbow", "zHandTwist_L", "Left wrist",
        "Right shoulder", "Right arm", "zArmTwist_R", "Right elbow", "zHandTwist_R", "Right wrist",
        "Thumb0_L", "Thumb1_L", "Thumb2_L", "IndexFinger1_L", "IndexFinger2_L", "IndexFinger3_L",
        "MiddleFinger1_L", "MiddleFinger2_L", "MiddleFinger3_L", "RingFinger1_L", "RingFinger2_L", "RingFinger3_L",
        "LittleFinger1_L", "LittleFinger2_L", "LittleFinger3_L",
        "Thumb0_R", "Thumb1_R", "Thumb2_R", "IndexFinger1_R", "IndexFinger2_R", "IndexFinger3_R",
        "MiddleFinger1_R", "MiddleFinger2_R", "MiddleFinger3_R", "RingFinger1_R", "RingFinger2_R", "RingFinger3_R",
        "LittleFinger1_R", "LittleFinger2_R", "LittleFinger3_R",
        "Left leg", "Left knee", "Left ankle", "Left toe", "Right leg", "Right knee", "Right ankle", "Right toe" };

    static int lastFrame = -1, seen;
    static Transform[] bones;
    static Transform armature;
    static SkinnedMeshRenderer eyes;
    static int blink = -1;
    static readonly StringBuilder data = new StringBuilder();
    static double startedAt;

    public static void Run()
    {
        EditorSceneManager.OpenScene("Assets/Scenes/Demo.unity");
        SessionState.SetBool(Flag, true);
        // This project enters play mode without a domain reload, so hook the recorder here too.
        startedAt = EditorApplication.timeSinceStartup;
        EditorApplication.update -= Tick;
        EditorApplication.update += Tick;
        EditorApplication.isPlaying = true;
    }

    static FurinaIdleRecorder()
    {
        if (!SessionState.GetBool(Flag, false)) return;
        startedAt = EditorApplication.timeSinceStartup;
        EditorApplication.update += Tick;
    }

    static void Tick()
    {
        if (EditorApplication.timeSinceStartup - startedAt > 600) Finish("timeout");
        if (!EditorApplication.isPlaying) return;
        Time.captureFramerate = 30;
        if (Time.frameCount == lastFrame) return;
        lastFrame = Time.frameCount;
        if (bones == null)
        {
            var player = GameObject.Find("Furina Player");
            if (!player) return;
            var all = new Dictionary<string, Transform>();
            var furina = player.transform.Find("ModelRoot/Furina");
            foreach (var t in furina.GetComponentsInChildren<Transform>(true)) all[t.name] = t;
            bones = new Transform[Body.Length];
            for (int i = 0; i < Body.Length; i++) all.TryGetValue(Body[i], out bones[i]);
            armature = all["Armature"];
            foreach (var r in furina.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                int b = r.sharedMesh ? r.sharedMesh.GetBlendShapeIndex("IdleBlink") : -1;
                if (b >= 0) { eyes = r; blink = b; break; }
            }
            data.Append("{\"fps\":30,\"bones\":[");
            for (int i = 0; i < Body.Length; i++) data.Append(i > 0 ? "," : "").Append('"').Append(Body[i]).Append('"');
            data.Append("],\"missing\":[");
            bool first = true;
            for (int i = 0; i < Body.Length; i++) if (!bones[i]) { data.Append(first ? "" : ",").Append('"').Append(Body[i]).Append('"'); first = false; }
            data.Append("],\"frames\":[");
        }
        seen++;
        if (seen <= SettleFrames) return;
        int index = seen - SettleFrames - 1;
        if (index >= RecordFrames) { data.Append("]}"); File.WriteAllText(OutPath, data.ToString()); Finish("ok"); return; }
        var c = CultureInfo.InvariantCulture;
        data.Append(index > 0 ? "," : "").Append("{\"r\":[");
        for (int i = 0; i < bones.Length; i++)
        {
            var q = bones[i] ? bones[i].localRotation : Quaternion.identity;
            data.Append(i > 0 ? "," : "").AppendFormat(c, "[{0:R},{1:R},{2:R},{3:R}]", q.x, q.y, q.z, q.w);
        }
        var hp = bones[0].localPosition;
        data.AppendFormat(c, "],\"hips\":[{0:R},{1:R},{2:R}],\"blink\":", hp.x, hp.y, hp.z)
            .Append((eyes ? eyes.GetBlendShapeWeight(blink) : 0f).ToString("R", c)).Append('}');
    }

    static void Finish(string why)
    {
        Debug.Log("[FurinaIdleRecorder] " + why);
        SessionState.SetBool(Flag, false);
        EditorApplication.update -= Tick;
        EditorApplication.Exit(why == "ok" ? 0 : 3);
    }
}
