using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.ThirdPerson
{
    [RequireComponent(typeof(CharacterController))]
    public class ThirdPersonMotor : MonoBehaviour
    {
        public Transform cameraTransform;
        public Transform visualRoot;
        public float walkSpeed = 4f;
        public bool flightMode = true;
        public float flySpeed = 20f;
        public float fastFlySpeed = 80f;
        public float sprintSpeed = 7f;
        public float jumpHeight = 1.2f;
        public float gravity = -22f;
        public float turnSpeed = 12f;
        CharacterController controller;
        float verticalSpeed;
        Vector3 spawn;

        void Awake() { controller = GetComponent<CharacterController>(); spawn = transform.position; }

        void Update()
        {
            var keyboard = Keyboard.current;
            var pad = Gamepad.current;
            Vector2 input = pad != null ? pad.leftStick.ReadValue() : Vector2.zero;
            if (keyboard != null)
            {
                input += new Vector2((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0),
                    (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
            }
            input = Vector2.ClampMagnitude(input, 1f);
            Vector3 forward = cameraTransform != null ? cameraTransform.forward : Vector3.forward;
            forward.y = 0f;
            forward.Normalize();
            Vector3 direction = forward * input.y + Vector3.Cross(Vector3.up, forward) * input.x;
            bool sprint = (keyboard != null && keyboard.leftShiftKey.isPressed) || (pad != null && pad.leftStickButton.isPressed);
            if (flightMode)
            {
                float up = keyboard == null ? 0f : (keyboard.spaceKey.isPressed ? 1f : 0f) - ((keyboard.leftCtrlKey.isPressed || keyboard.rightCtrlKey.isPressed) ? 1f : 0f);
                Vector3 flight = Vector3.ClampMagnitude(direction + Vector3.up * up, 1f);
                controller.Move(flight * (sprint ? fastFlySpeed : flySpeed) * Time.deltaTime);
                verticalSpeed = 0f;
                if (direction.sqrMagnitude > .001f && visualRoot != null)
                    visualRoot.rotation = Quaternion.Slerp(visualRoot.rotation, Quaternion.LookRotation(direction), 1f - Mathf.Exp(-turnSpeed * Time.deltaTime));
                return;
            }
            bool jump = (keyboard != null && keyboard.spaceKey.wasPressedThisFrame) || (pad != null && pad.buttonSouth.wasPressedThisFrame);
            if (controller.isGrounded)
            {
                verticalSpeed = -2f;
                if (jump) verticalSpeed = Mathf.Sqrt(jumpHeight * -2f * gravity);
            }
            verticalSpeed += gravity * Time.deltaTime;
            controller.Move((direction * (sprint ? sprintSpeed : walkSpeed) + Vector3.up * verticalSpeed) * Time.deltaTime);
            if (direction.sqrMagnitude > 0.001f && visualRoot != null)
                visualRoot.rotation = Quaternion.Slerp(visualRoot.rotation, Quaternion.LookRotation(direction), 1f - Mathf.Exp(-turnSpeed * Time.deltaTime));
            if (transform.position.y < spawn.y - 100f)
            {
                controller.enabled = false;
                transform.position = spawn;
                verticalSpeed = 0f;
                controller.enabled = true;
            }
        }
    }
}
