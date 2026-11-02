using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Game.ThirdPerson;
using UnityEngine.Rendering.HighDefinition;

public static class UntitledCharacterSetup
{
    const string Root = "Assets/Game/Characters/Untitled";
    [Serializable] public class MaterialEntry { public string name; public float[] color; public string texture; }
    [Serializable] public class Manifest { public MaterialEntry[] materials; }
    static Bounds BoundsOf(GameObject go)
    {
        var renderers = go.GetComponentsInChildren<Renderer>(true);
        if (renderers.Length == 0) throw new Exception("Character has no renderers.");
        var b = renderers[0].bounds;
        foreach (var r in renderers.Skip(1)) b.Encapsulate(r.bounds);
        return b;
    }
    [MenuItem("Tools/Character/Install Untitled Character")]
    public static void Install()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play mode before installing.");
        var player = GameObject.Find("ThirdPersonRig/Player");
        if (!player) throw new Exception("ThirdPersonRig/Player not found in the active scene.");
        var motor = player.GetComponent<ThirdPersonMotor>();
        var visualRoot = motor.visualRoot;
        if (!visualRoot) throw new Exception("Player visualRoot not assigned.");
        if (visualRoot.Find("UntitledCharacter")) throw new Exception("Character is already installed.");
        string modelPath = Root + "/UntitledCharacter.fbx";
        var importer = AssetImporter.GetAtPath(modelPath) as ModelImporter;
        if (!importer) throw new Exception("Character FBX is missing.");
        var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(Root + "/CharacterManifest.json"));
        Directory.CreateDirectory(Root + "/Materials");
        AssetDatabase.Refresh();
        var shader = Shader.Find("HDRP/Lit");
        if (!shader) throw new Exception("HDRP/Lit shader is unavailable.");
        foreach (var entry in manifest.materials)
        {
            string path = Root + "/Materials/" + entry.name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (!material) { material = new Material(shader); AssetDatabase.CreateAsset(material, path); }
            material.shader = shader;
            var texture = string.IsNullOrEmpty(entry.texture) ? null :
                AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Textures/" + entry.texture);
            material.SetColor("_BaseColor", texture ? Color.white :
                new Color(entry.color[0], entry.color[1], entry.color[2], entry.color[3]));
            material.SetTexture("_BaseColorMap", texture);
            material.SetFloat("_Metallic", 0f);
            material.SetFloat("_Smoothness", .22f);
            material.SetFloat("_DoubleSidedEnable", 1f);
            material.SetFloat("_AlphaCutoffEnable", texture ? 1f : 0f);
            material.SetFloat("_AlphaCutoff", .35f);
            HDMaterial.ValidateMaterial(material);
            EditorUtility.SetDirty(material);
            importer.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material),entry.name),material);
        }
        importer.animationType = ModelImporterAnimationType.Generic;
        importer.importAnimation = false;
        importer.optimizeGameObjects = false;
        importer.isReadable = true;
        importer.SaveAndReimport();
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
        var character = (GameObject)PrefabUtility.InstantiatePrefab(model,visualRoot);
        Undo.RegisterCreatedObjectUndo(character,"Install Untitled character");
        character.name = "UntitledCharacter";
        character.transform.localPosition = Vector3.zero;
        character.transform.localRotation = Quaternion.identity;
        character.transform.localScale = Vector3.one;
        var bounds = BoundsOf(character);
        if (bounds.size.y < .001f) throw new Exception("Invalid model height.");
        character.transform.localScale *= 1.75f / bounds.size.y;
        bounds = BoundsOf(character);
        character.transform.position += visualRoot.position -
            new Vector3(bounds.center.x,bounds.min.y,bounds.center.z);
        foreach (var skin in character.GetComponentsInChildren<SkinnedMeshRenderer>())
        {
            skin.quality = SkinQuality.Bone4;
            skin.updateWhenOffscreen = true;
        }
        var animator = character.GetComponent<Animator>();
        if (animator) animator.enabled = false;
        var motion = Undo.AddComponent<UntitledCharacterMotion>(character);
        motion.Configure(player.transform,motor);
        EditorUtility.SetDirty(motion);
        var placeholder = visualRoot.Find("Placeholder_ReplaceWithCharacterModel");
        if (placeholder) { Undo.RecordObject(placeholder.gameObject,"Hide capsule placeholder"); placeholder.gameObject.SetActive(false); }
        AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(player.scene);
        EditorSceneManager.SaveScene(player.scene);
        Selection.activeGameObject = character;
        if (SceneView.lastActiveSceneView) SceneView.lastActiveSceneView.Frame(new Bounds(character.transform.position+Vector3.up*.85f,Vector3.one*2.4f),false);
        Report();
    }
    [MenuItem("Tools/Character/Validate Untitled Character")]
    public static void Report()
    {
        var player = GameObject.Find("ThirdPersonRig/Player");
        var character = player.transform.Find("ModelRoot/UntitledCharacter").gameObject;
        var motion = character.GetComponent<UntitledCharacterMotion>();
        var bounds = BoundsOf(character);
        Debug.Log("CHARACTER_REPORT " + JsonUtility.ToJson(new ReportData {
            scene=player.scene.path, renderers=character.GetComponentsInChildren<SkinnedMeshRenderer>().Length,
            joints=motion.joints.Count(j=>j.bone),controller=player.GetComponent<CharacterController>().enabled,
            placeholderActive=player.transform.Find("ModelRoot/Placeholder_ReplaceWithCharacterModel").gameObject.activeSelf,
            height=bounds.size.y, playing=Application.isPlaying,frame=Time.frameCount,
            phase=new SerializedObject(motion).FindProperty("motionPhase").floatValue,
            arm=motion.joints[2].bone.localRotation.eulerAngles
        }));
    }
    [Serializable] class ReportData {
        public string scene; public int renderers,joints,frame; public bool controller,placeholderActive,playing;
        public float height,phase; public Vector3 arm;
    }
    [MenuItem("Tools/Character/Preview Walk Pose")]
    public static void PreviewWalk()
    {
        var motion=GameObject.Find("ThirdPersonRig/Player/ModelRoot/UntitledCharacter").GetComponent<UntitledCharacterMotion>();
        motion.ApplyPose(1f,1.3f,1f,false);
        SceneView.RepaintAll();
    }
    [MenuItem("Tools/Character/Restore Bind Pose")]
    public static void RestorePose()
    {
        var motion=GameObject.Find("ThirdPersonRig/Player/ModelRoot/UntitledCharacter").GetComponent<UntitledCharacterMotion>();
        foreach(var j in motion.joints) if(j.bone) j.bone.localRotation=j.rest;
        SceneView.RepaintAll();
    }

    [MenuItem("Tools/Character/Refresh Motion Rig")]
    public static void RefreshRig()
    {
        var player=GameObject.Find("ThirdPersonRig/Player");
        var motion=player.transform.Find("ModelRoot/UntitledCharacter").GetComponent<UntitledCharacterMotion>();
        foreach(var j in motion.joints) if(j.bone) j.bone.localRotation=j.rest;
        var b=BoundsOf(motion.gameObject);
        motion.transform.position+=Vector3.up*(player.transform.position.y-b.min.y);
        motion.Configure(player.transform,player.GetComponent<ThirdPersonMotor>());
        EditorUtility.SetDirty(motion);
        EditorSceneManager.MarkSceneDirty(player.scene);
        EditorSceneManager.SaveScene(player.scene);
        Report();
    }
    [MenuItem("Tools/Character/Verify Skin Motion")]
    public static void VerifySkinMotion()
    {
        var motion=GameObject.Find("ThirdPersonRig/Player/ModelRoot/UntitledCharacter").GetComponent<UntitledCharacterMotion>();
        var position=motion.transform.localPosition;
        var rotation=motion.transform.localRotation;
        var renderers=motion.GetComponentsInChildren<SkinnedMeshRenderer>();
        var meshes=renderers.Select(r=>new Mesh()).ToArray();
        try
        {
            motion.ApplyPose(0f,0f,0f,false);
            for(int i=0;i<renderers.Length;i++) renderers[i].BakeMesh(meshes[i]);
            var idle=meshes.Select(m=>m.vertices).ToArray();
            motion.ApplyPose(1f,1.3f,1f,false);
            int changed=0; float maxDistance=0f;
            for(int i=0;i<renderers.Length;i++)
            {
                renderers[i].BakeMesh(meshes[i]);
                var vertices=meshes[i].vertices;
                for(int j=0;j<vertices.Length;j++)
                {
                    float distance=(vertices[j]-idle[i][j]).magnitude;
                    if(distance>.0001f) changed++;
                    maxDistance=Mathf.Max(maxDistance,distance);
                }
            }
            if(changed<100) throw new Exception("Walking pose did not deform the skinned meshes.");
            Debug.Log("CHARACTER_SKIN_TEST changedVertices="+changed+" maxLocalDisplacement="+maxDistance);
        }
        finally
        {
            foreach(var j in motion.joints) if(j.bone) j.bone.localRotation=j.rest;
            motion.transform.localPosition=position;
            motion.transform.localRotation=rotation;
            foreach(var mesh in meshes) UnityEngine.Object.DestroyImmediate(mesh);
        }
    }
    [MenuItem("Tools/Character/Show Character Closeup")]
    public static void ShowCharacter()
    {
        var character=GameObject.Find("ThirdPersonRig/Player/ModelRoot/UntitledCharacter");
        var view=SceneView.lastActiveSceneView;
        view.sceneLighting=false;
        view.drawGizmos=false;
        view.LookAt(BoundsOf(character).center,Quaternion.Euler(8f,180f,0f),1.5f,false,true);
        Selection.activeGameObject=character;
        view.Repaint();
    }
    [MenuItem("Tools/Character/Restore Scene Lighting")]
    public static void RestoreSceneLighting()
    {
        SceneView.lastActiveSceneView.sceneLighting=true;
        SceneView.lastActiveSceneView.drawGizmos=true;
        SceneView.RepaintAll();
    }

}
