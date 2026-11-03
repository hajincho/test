using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.ThirdPerson
{
    [DisallowMultipleComponent]
    [RequireComponent(typeof(ThirdPersonMotor))]
    public sealed class CharacterAppearanceSwitch : MonoBehaviour
    {
        [SerializeField] GameObject blenderCharacterPrefab;
        public int SelectedCharacter { get; private set; } = 1;

        UntitledCharacterMotion original;
        GameObject alternate;
        ThirdPersonFollowCamera followCamera;
        Renderer[] originalRenderers, alternateRenderers;
        bool[] originalHidden, alternateHidden;

        void Start()
        {
            var motor = GetComponent<ThirdPersonMotor>();
            original = GetComponentInChildren<UntitledCharacterMotion>(true);
            if (!original || !blenderCharacterPrefab)
            {
                Debug.LogError("Character switching needs the original rig and a Blender character prefab.", this);
                enabled = false;
                return;
            }

            followCamera = motor.cameraTransform ? motor.cameraTransform.GetComponent<ThirdPersonFollowCamera>() : null;
            originalRenderers = original.GetComponentsInChildren<Renderer>(true);
            alternate = Instantiate(blenderCharacterPrefab, original.transform.parent, false);
            alternate.name = blenderCharacterPrefab.name;
            alternateRenderers = alternate.GetComponentsInChildren<Renderer>(true);
            originalHidden = RememberVisibility(originalRenderers);
            alternateHidden = RememberVisibility(alternateRenderers);

            // Both rigs keep evaluating the same pose, including feet and secondary motion.
            // Only the currently selected appearance contributes geometry or shadows.
            if (originalRenderers.Length > 0)
            {
                var source = originalRenderers[0];
                foreach (var r in alternateRenderers)
                {
                    r.gameObject.layer = source.gameObject.layer;
                    r.renderingLayerMask = source.renderingLayerMask;
                    r.lightProbeUsage = source.lightProbeUsage;
                    r.receiveShadows = source.receiveShadows;
                }
            }
            Show(alternateRenderers, alternateHidden, false);
        }

        void Update()
        {
            var keyboard = Keyboard.current;
            if (keyboard == null) return;
            if (keyboard.digit1Key.wasPressedThisFrame || keyboard.numpad1Key.wasPressedThisFrame)
                SelectCharacter(1);
            else if (keyboard.digit2Key.wasPressedThisFrame || keyboard.numpad2Key.wasPressedThisFrame)
                SelectCharacter(2);
        }

        public void SelectCharacter(int number)
        {
            if (!alternate || !original || number == SelectedCharacter || (number != 1 && number != 2)) return;
            bool useOriginal = number == 1;
            if (followCamera) followCamera.SetCharacterRoot(useOriginal ? original.transform : alternate.transform);
            Show(originalRenderers, originalHidden, useOriginal);
            Show(alternateRenderers, alternateHidden, !useOriginal);
            SelectedCharacter = number;
        }

        static bool[] RememberVisibility(Renderer[] parts)
        {
            var hidden = new bool[parts.Length];
            for (int i = 0; i < parts.Length; i++) hidden[i] = parts[i].forceRenderingOff;
            return hidden;
        }

        static void Show(Renderer[] parts, bool[] wasHidden, bool visible)
        {
            for (int i = 0; i < parts.Length; i++)
                if (parts[i]) parts[i].forceRenderingOff = !visible || wasHidden[i];
        }

        void OnDisable() => SelectCharacter(1);

        void OnDestroy()
        {
            if (alternate) Destroy(alternate);
        }
    }
}
