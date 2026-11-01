using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.ThirdPerson
{
    public class ThirdPersonFollowCamera : MonoBehaviour
    {
        public Transform target;
        public float distance = 5f;
        public float minDistance = 2f;
        public float maxDistance = 9f;
        public float pitch = 18f;
        public float yaw;
        public float mouseSensitivity = 0.15f;
        public LayerMask collisionMask = ~0;

        void LateUpdate()
        {
            if (target == null) return;
            var mouse = Mouse.current;
            var pad = Gamepad.current;
            Vector2 look = pad != null ? pad.rightStick.ReadValue() * (120f * Time.deltaTime) : Vector2.zero;
            if (mouse != null)
            {
                look += mouse.delta.ReadValue() * mouseSensitivity;
                distance = Mathf.Clamp(distance - mouse.scroll.ReadValue().y * 0.05f, minDistance, maxDistance);
            }
            yaw += look.x;
            pitch = Mathf.Clamp(pitch - look.y, -25f, 70f);
            var rotation = Quaternion.Euler(pitch, yaw, 0f);
            Vector3 backward = rotation * Vector3.back;
            float safeDistance = distance;
            if (Physics.SphereCast(target.position, 0.2f, backward, out var hit, distance, collisionMask, QueryTriggerInteraction.Ignore))
                safeDistance = Mathf.Max(0.1f, hit.distance - 0.1f);
            transform.SetPositionAndRotation(target.position + backward * safeDistance, rotation);
        }
    }
}
