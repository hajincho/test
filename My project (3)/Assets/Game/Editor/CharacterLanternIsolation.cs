using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.HighDefinition;
using System.Linq;
using HDMask = UnityEngine.Rendering.HighDefinition.RenderingLayerMask;

public static class CharacterLanternIsolation
{
    [MenuItem("Tools/Character/Isolate Lantern From Character")]
    public static void Apply()
    {
        if (EditorApplication.isPlaying) throw new System.Exception("Stop play mode first.");
        var player = GameObject.Find("ThirdPersonRig/Player");
        var model = player.transform.Find("ModelRoot/UntitledCharacter");
        var lantern = player.transform.Find("CharacterLantern").GetComponent<Light>();
        var lanternHD = lantern.GetComponent<HDAdditionalLightData>();
        var cameraHD = Camera.main.GetComponent<HDAdditionalCameraData>();
        var renderers = model.GetComponentsInChildren<SkinnedMeshRenderer>(true);
        if (renderers.Length != 22 || !lanternHD || !cameraHD) throw new System.Exception("Required scene objects are missing.");
        foreach(var r in renderers)
        {
            Undo.RecordObject(r,"Character light layer");
            r.renderingLayerMask = (r.renderingLayerMask & ~255u) | 2u;
        }
        int lights = 0, probes = 0;
        foreach(var light in Resources.FindObjectsOfTypeAll<HDAdditionalLightData>().Where(x=>x.gameObject.scene.isLoaded && x != lanternHD))
        {
            uint mask = light.GetLightLayers();
            if ((mask & 1u) == 0) continue;
            Undo.RecordObject(light,"Preserve character illumination");
            Undo.RecordObject(light.GetComponent<Light>(),"Preserve character illumination");
            light.lightlayersMask = (HDMask)(mask | 2u);
            EditorUtility.SetDirty(light);
            lights++;
        }
        foreach(var probe in Resources.FindObjectsOfTypeAll<HDProbe>().Where(x=>x.gameObject.scene.isLoaded))
        {
            uint mask = probe.lightLayersAsUInt;
            if ((mask & 1u) == 0) continue;
            Undo.RecordObject(probe,"Preserve character reflection");
            probe.lightLayers = (HDMask)(mask | 2u);
            EditorUtility.SetDirty(probe);
            probes++;
        }
        Undo.RecordObject(lanternHD,"Lantern light layer");
        lanternHD.lightlayersMask = (HDMask)1u;
        Undo.RecordObject(cameraHD,"Enable camera light layers");
        if (!cameraHD.customRenderingSettings) cameraHD.renderingPathCustomFrameSettingsOverrideMask = default;
        cameraHD.customRenderingSettings = true;
        cameraHD.renderingPathCustomFrameSettings.SetEnabled(FrameSettingsField.LightLayers,true);
        cameraHD.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)FrameSettingsField.LightLayers] = true;
        EditorUtility.SetDirty(cameraHD);
        EditorSceneManager.MarkSceneDirty(player.scene);
        EditorSceneManager.SaveScene(player.scene);
        Debug.Log("HDRP_LANTERN_ISOLATION renderers="+renderers.Length+" characterMask="+renderers[0].renderingLayerMask+" lanternMask="+lanternHD.GetLightLayers()+" otherLights="+lights+" probes="+probes+" cameraLightLayers="+cameraHD.renderingPathCustomFrameSettings.IsEnabled(FrameSettingsField.LightLayers));
    }
}