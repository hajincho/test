using UnityEngine;

namespace Game.ThirdPerson
{
    // Complements UntitledCharacterMotion after its base pose is evaluated.
    // No Animator avatar or humanoid mapping is required.
    [DefaultExecutionOrder(180)]
    public sealed class CharacterGroundAndLook : MonoBehaviour
    {
        public Transform playerRoot;
        public Transform visualRoot;
        public Transform lookCamera;
        public LayerMask groundLayers = ~0;
        [Range(0f, 1f)] public float footWeight = 1f;
        [Range(0f, 1f)] public float lookWeight = .75f;
        public float maxFootAdjustment = .3f;
        public float maxHeadYaw = 55f;
        public float maxHeadPitch = 35f;

        private ThirdPersonMotor motor;
        private UntitledCharacterMotion motion;
        private Transform head;
        private Leg left, right, leftAux, rightAux;
        private float groundedBlend, headYaw, headPitch;
        private Quaternion stableHeadRotation;
        private bool hasStableHeadRotation;

        private void OnEnable() { hasStableHeadRotation = false; }
        private readonly RaycastHit[] hits = new RaycastHit[16];

        private sealed class Leg
        {
            public Transform thigh, shin, foot;
            public float restFootHeight;
            public float targetHeight, weight;
            public Quaternion restFootRotation;
            public Vector3 normal = Vector3.up;
            public bool planted;
            public Vector3 contactPosition;
        }

        private Transform FindBone(string name)
        {
            foreach (var t in GetComponentsInChildren<Transform>(true))
                if (t.name == name) return t;
            return null;
        }

        private Leg MakeLeg(string upper, string lower, string footName)
        {
            var leg = new Leg { thigh = FindBone(upper), shin = FindBone(lower), foot = FindBone(footName) };
            if (!leg.thigh || !leg.shin || !leg.foot) return null;
            leg.restFootHeight = leg.foot.position.y - playerRoot.position.y;
            leg.restFootRotation = leg.foot.localRotation;
            leg.targetHeight = leg.foot.position.y;
            return leg;
        }

        private void Awake()
        {
            if (!playerRoot)
            {
                var found = GetComponentInParent<ThirdPersonMotor>();
                if (found) playerRoot = found.transform;
            }
            if (!playerRoot) { enabled = false; return; }
            motor = playerRoot.GetComponent<ThirdPersonMotor>();
            motion = GetComponent<UntitledCharacterMotion>();
            if (!visualRoot && motor) visualRoot = motor.visualRoot;
            if (!visualRoot) visualRoot = playerRoot;
            if (!lookCamera && motor) lookCamera = motor.cameraTransform;
            if (!lookCamera && Camera.main) lookCamera = Camera.main.transform;
            head = FindBone("Head");
            left = MakeLeg("Thigh_L", "Shin_L", "Foot_L");
            right = MakeLeg("Thigh_R", "Shin_R", "Foot_R");
            leftAux = MakeLeg("ThighAux_L", "ShinAux_L", "Bone_015");
            rightAux = MakeLeg("ThighAux_R", "ShinAux_R", "Bone_025");
        }

        private void LateUpdate()
        {
            float dt = Time.deltaTime;
            if (dt <= 0f || !playerRoot) return;
            float k = 1f - Mathf.Exp(-12f * dt);
            groundedBlend = Mathf.Lerp(groundedBlend, !motor || motor.Grounded ? 1f : 0f, k);
            AdjustLeg(left, dt);
            AdjustLeg(right, dt);
            AdjustLeg(leftAux, dt);
            AdjustLeg(rightAux, dt);
            AimHead(dt);
        }

        private void AdjustLeg(Leg leg, float dt)
        {
            if (leg == null || !leg.foot || !leg.thigh || !leg.shin) return;
            leg.foot.localRotation = leg.restFootRotation;
            if (motor && motor.IsJumping)
            {
                leg.planted = false;
                leg.weight = 0f;
                leg.targetHeight = leg.foot.position.y;
                return;
            }
            Vector3 foot = leg.foot.position;
            Vector3 origin = foot + Vector3.up * .45f;
            int count = Physics.RaycastNonAlloc(origin, Vector3.down, hits, 1.2f, groundLayers, QueryTriggerInteraction.Ignore);
            float closest = float.PositiveInfinity;
            RaycastHit best = default;
            for (int i = 0; i < count; i++)
            {
                var hit = hits[i];
                if (!hit.collider || hit.collider.transform.IsChildOf(playerRoot)) continue;
                if (hit.normal.y < .45f || hit.distance >= closest) continue;
                closest = hit.distance;
                best = hit;
            }

            float desiredWeight = 0f;
            float desiredHeight = foot.y;
            Vector3 normal = Vector3.up;
            if (!float.IsInfinity(closest))
            {
                float onGround = best.point.y + leg.restFootHeight;
                float delta = onGround - foot.y;
                // Let a swinging foot lift; correct only the planted part of the stride.
                float contact = 1f - Mathf.InverseLerp(.04f, .22f, Mathf.Max(0f, -delta));
                desiredWeight = footWeight * groundedBlend * contact;
                desiredHeight = foot.y + Mathf.Clamp(delta, -maxFootAdjustment, maxFootAdjustment);
                normal = best.normal;
            }

            // Opposite legs contact half a cycle apart. Hold the ankle in world space
            // through support, and release before the knee starts its recovery.
            float lockWeight = 0f;
            if (motion && motion.enabled && motion.RunContactWeight > .1f && motor && motor.Grounded && best.collider)
            {
                bool rightSide = leg == right || leg == rightAux;
                float cycle = Mathf.Repeat(motion.GaitPhase / (2f * Mathf.PI) + (rightSide ? .5f : 0f) + .16f, 1f);
                if (cycle < .32f)
                {
                    if (!leg.planted) leg.contactPosition = foot;
                    leg.planted = true;
                    float edge = Mathf.Clamp01(Mathf.Min(cycle, .32f - cycle) / .045f);
                    lockWeight = Mathf.SmoothStep(0f, 1f, edge) * motion.RunContactWeight * footWeight;
                    desiredHeight = Mathf.Lerp(desiredHeight, best.point.y + leg.restFootHeight, lockWeight);
                    desiredWeight = Mathf.Max(desiredWeight, lockWeight);
                }
                else leg.planted = false;
            }
            else leg.planted = false;

            float blend = 1f - Mathf.Exp(-14f * dt);
            leg.weight = Mathf.Lerp(leg.weight, desiredWeight, blend);
            leg.targetHeight = Mathf.Lerp(leg.targetHeight, desiredHeight, blend);
            leg.normal = Vector3.Slerp(leg.normal, normal, blend).normalized;
            if (leg.weight < .005f) return;

            Vector3 target = Vector3.Lerp(foot, leg.contactPosition, lockWeight);
            target.y = Mathf.Lerp(foot.y, leg.targetHeight, leg.weight);
            SolveTwoBone(leg, target, Mathf.Max(lockWeight, leg.weight));

            // Rotate only modestly; the imported rig may already have a stylized foot angle.
            Quaternion align = Quaternion.FromToRotation(visualRoot.up, leg.normal);
            leg.foot.rotation = Quaternion.Slerp(leg.foot.rotation, align * leg.foot.rotation, .55f * leg.weight);
        }

        private void SolveTwoBone(Leg leg, Vector3 target, float weight)
        {
            Vector3 hip = leg.thigh.position;
            Vector3 knee = leg.shin.position;
            Vector3 ankle = leg.foot.position;
            float upper = Vector3.Distance(hip, knee);
            float lower = Vector3.Distance(knee, ankle);
            Vector3 toTarget = target - hip;
            float distance = toTarget.magnitude;
            if (upper < .001f || lower < .001f || distance < .001f) return;

            Vector3 direction = toTarget / distance;
            float clamped = Mathf.Clamp(distance, Mathf.Abs(upper - lower) + .001f, upper + lower - .001f);
            float along = (upper * upper - lower * lower + clamped * clamped) / (2f * clamped);
            float height = Mathf.Sqrt(Mathf.Max(0f, upper * upper - along * along));
            Vector3 bend = Vector3.ProjectOnPlane(knee - hip, direction);
            if (bend.sqrMagnitude < .00001f)
                bend = Vector3.ProjectOnPlane(visualRoot.forward, direction);
            if (bend.sqrMagnitude < .00001f) return;
            bend.Normalize();
            Vector3 desiredKnee = hip + direction * along + bend * height;

            var upperRotation = Quaternion.FromToRotation(knee - hip, desiredKnee - hip);
            leg.thigh.rotation = Quaternion.Slerp(leg.thigh.rotation, upperRotation * leg.thigh.rotation, weight);
            knee = leg.shin.position;
            ankle = leg.foot.position;
            var lowerRotation = Quaternion.FromToRotation(ankle - knee, target - knee);
            leg.shin.rotation = Quaternion.Slerp(leg.shin.rotation, lowerRotation * leg.shin.rotation, weight);
        }

        private void AimHead(float dt)
        {
            if (!head || !lookCamera || !visualRoot) return;
            Vector3 look = visualRoot.InverseTransformDirection(lookCamera.forward).normalized;
            float yaw = Mathf.Clamp(Mathf.Atan2(look.x, look.z) * Mathf.Rad2Deg, -maxHeadYaw, maxHeadYaw);
            float pitch = Mathf.Clamp(Mathf.Asin(Mathf.Clamp(look.y, -1f, 1f)) * Mathf.Rad2Deg, -maxHeadPitch, maxHeadPitch);
            float smooth = 1f - Mathf.Exp(-8f * dt);
            headYaw = Mathf.LerpAngle(headYaw, yaw * lookWeight, smooth);
            headPitch = Mathf.Lerp(headPitch, pitch * lookWeight, smooth);
            head.rotation = Quaternion.AngleAxis(headYaw, visualRoot.up) *
                            Quaternion.AngleAxis(-headPitch, visualRoot.right) * head.rotation;

            // Filter gait-induced rotation in character space while preserving look and body turns.
            Quaternion desired = Quaternion.Inverse(visualRoot.rotation) * head.rotation;
            if (!hasStableHeadRotation)
            {
                stableHeadRotation = desired;
                hasStableHeadRotation = true;
            }
            float gait = motor ? Mathf.Clamp01(motor.PlanarSpeed / Mathf.Max(motor.walkSpeed, .1f)) : 0f;
            stableHeadRotation = Quaternion.Slerp(stableHeadRotation, desired, 1f - Mathf.Exp(-Mathf.Lerp(5f, 2.5f, gait) * dt));
            head.rotation = visualRoot.rotation * stableHeadRotation;
        }
    }
}
