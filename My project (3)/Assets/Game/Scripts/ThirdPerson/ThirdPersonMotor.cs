using UnityEngine;
using UnityEngine.InputSystem;

namespace Game.ThirdPerson
{
    [RequireComponent(typeof(CharacterController))]
    public class ThirdPersonMotor : MonoBehaviour
    {
        public Transform cameraTransform;
        public Transform visualRoot;
        public float walkSpeed = 1.2f;
        public bool flightMode = false;
        public float flySpeed = 20f;
        public float fastFlySpeed = 80f;
        public float sprintSpeed = 4f;
        public float jumpHeight = .8f;
        public float gravity = -9.81f;
        public float turnSpeed = 12f;
        public bool Grounded { get; private set; }
        public float VerticalSpeed => verticalSpeed;
        public float PlanarSpeed { get; private set; }
        public bool Sprinting { get; private set; }
        CharacterController controller;
        float verticalSpeed;
        Vector3 spawn;
        float lastGrounded = -10f, lastJumpPressed = -10f;
        public bool SimulationInput { get; set; }
        public Vector2 SimulatedMove { get; set; }
        public bool SimulatedSprint { get; set; }
        public bool SimulatedJump { get; set; }

        void Awake() { controller = GetComponent<CharacterController>(); spawn = transform.position; }
        void Update()
        {
            var keyboard = Keyboard.current;
            var pad = Gamepad.current;
            Vector2 input = pad != null ? pad.leftStick.ReadValue() : Vector2.zero;
            if (keyboard != null)
                input += new Vector2((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0),
                    (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
            bool sprint = (keyboard != null && keyboard.leftShiftKey.isPressed) || (pad != null && pad.leftStickButton.isPressed);
            bool jump = (keyboard != null && keyboard.spaceKey.wasPressedThisFrame) || (pad != null && pad.buttonSouth.wasPressedThisFrame);
            if (SimulationInput) { input = SimulatedMove; sprint = SimulatedSprint; jump = SimulatedJump; SimulatedJump = false; }
            Tick(input, sprint, jump, Time.deltaTime);
        }
        public void Tick(Vector2 input, bool sprint, bool jump, float dt)
        {
            if (!controller) controller = GetComponent<CharacterController>();
            if (dt <= 0f) return;
            input = Vector2.ClampMagnitude(input, 1f);
            // Camera yaw remains well-defined even when looking straight up.
            float yaw = cameraTransform ? cameraTransform.eulerAngles.y : 0f;
            Vector3 direction = Quaternion.Euler(0f, yaw, 0f) * new Vector3(input.x, 0f, input.y);
            Grounded = controller.isGrounded;
            if (Grounded) lastGrounded = Time.time;
            if (jump) lastJumpPressed = Time.time;
            if (Grounded && verticalSpeed < 0f) verticalSpeed = -2f;
            if (Time.time - lastJumpPressed < .12f && Time.time - lastGrounded < .1f)
            {
                verticalSpeed = Mathf.Sqrt(2f * Mathf.Abs(gravity) * jumpHeight);
                lastJumpPressed = -10f; lastGrounded = -10f; Grounded = false;
            }
            float previousVertical = verticalSpeed;
            verticalSpeed = Mathf.Max(verticalSpeed + gravity * dt, -50f);
            float verticalDisplacement = (previousVertical + verticalSpeed) * .5f * dt;
            Vector3 before = transform.position;
            var flags = controller.Move(direction * (sprint ? sprintSpeed : walkSpeed) * dt + Vector3.up * verticalDisplacement);
            if ((flags & CollisionFlags.Above) != 0 && verticalSpeed > 0f) verticalSpeed = 0f;
            Grounded = (flags & CollisionFlags.Below) != 0;
            Vector3 delta = transform.position - before;
            PlanarSpeed = new Vector2(delta.x, delta.z).magnitude / dt;
            Sprinting = sprint && PlanarSpeed > .1f;
            if (direction.sqrMagnitude > .001f && visualRoot)
                visualRoot.rotation = Quaternion.Slerp(visualRoot.rotation, Quaternion.LookRotation(direction), 1f - Mathf.Exp(-turnSpeed * dt));
            if (transform.position.y < spawn.y - 100f)
            {
                controller.enabled = false; transform.position = spawn;
                verticalSpeed = 0f; controller.enabled = true;
            }
        }
    }
}