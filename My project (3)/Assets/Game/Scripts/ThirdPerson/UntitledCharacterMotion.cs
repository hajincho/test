using System;
using UnityEngine;

namespace Game.ThirdPerson
{
    [DefaultExecutionOrder(100)]
    public sealed class UntitledCharacterMotion : MonoBehaviour
    {
        [Serializable] public class Joint
        {
            public Transform bone;
            public Quaternion rest;
            public Vector3 pitchAxis;
            public Vector3 rollAxis;
            public float side;
        }
        public Transform movementRoot;
        public ThirdPersonMotor motor;
        public Joint[] joints;
        public float walkingAmplitude = 24f;
        public float breathingAmplitude = .008f;
        [SerializeField] float currentSpeed;
        [SerializeField] float motionPhase;
        sealed class FingerJoint
        {
            public Transform bone;
            public Quaternion rest;
            public Vector3 curlAxis;
            public float curlDegrees;
        }
        FingerJoint[] fingers;
        Transform[] clothBones;
        Quaternion[] clothRest;
        Vector3[] clothAxes;
        float windBlend;
        Transform[] hairBones;
        Quaternion[] hairRest;
        Vector3[] hairAxes;
        Vector3 restPosition;
        Quaternion restRotation;
        Vector3 previousPosition;
        float movement;
        float clock;

        public void Configure(Transform root, ThirdPersonMotor movementMotor)
        {
            movementRoot = root;
            motor = movementMotor;
            restPosition = transform.localPosition;
            restRotation = transform.localRotation;
            string[] names = { "Chest", "Head", "UpperArm_L", "UpperArm_R", "Forearm_L", "Forearm_R",
                "Thigh_L", "Thigh_R", "Shin_L", "Shin_R", "ThighAux_L", "ThighAux_R", "ShinAux_L", "ShinAux_R" };
            var all = GetComponentsInChildren<Transform>(true);
            joints = new Joint[names.Length];
            for (int i = 0; i < names.Length; i++)
            {
                var bone = Array.Find(all, t => t.name == names[i]);
                joints[i] = new Joint { bone = bone };
                if (!bone) continue;
                joints[i].rest = bone.localRotation;
                joints[i].side = Mathf.Sign(transform.InverseTransformPoint(bone.position).x);
                joints[i].pitchAxis = bone.InverseTransformDirection(transform.right).normalized;
                joints[i].rollAxis = bone.InverseTransformDirection(transform.forward).normalized;
            }
        }
        void OnEnable()
        {
            restPosition = transform.localPosition;
            restRotation = transform.localRotation;
            previousPosition = movementRoot ? movementRoot.position : transform.position;
            lastYaw = transform.parent ? transform.parent.eulerAngles.y : transform.eulerAngles.y;
            turnLean = 0f;
            CacheFingers();
            CacheCloth();
        }
        void CacheFingers()
        {
            int[] starts = { 246, 250, 254, 258, 262, 284, 288, 292, 296, 300 };
            var all = GetComponentsInChildren<Transform>(true);
            var found = new System.Collections.Generic.List<FingerJoint>();
            for (int chain = 0; chain < starts.Length; chain++)
            {
                for (int segment = 0; segment < 3; segment++)
                {
                    string boneName = "Bone_" + (starts[chain] + segment);
                    Transform bone = Array.Find(all, t => t.name == boneName);
                    if (!bone || bone.childCount == 0) continue;
                    Vector3 direction = (bone.GetChild(0).position - bone.position).normalized;
                    Vector3 axis = Vector3.Cross(direction, -transform.up);
                    if (axis.sqrMagnitude < .0001f) axis = transform.forward;
                    found.Add(new FingerJoint {
                        bone = bone, rest = bone.localRotation,
                        curlAxis = bone.InverseTransformDirection(axis.normalized),
                        curlDegrees = chain % 5 == 0 ? 42f : (segment == 0 ? 58f : 72f)
                    });
                }
            }
            fingers = found.ToArray();
        }
        void CacheCloth()
        {
            // Waist-attached skirt chains in the imported character rig.
            int[] ids = { 35, 36, 42, 43, 53, 54, 64, 65, 75, 76, 86, 87,
                          97, 98, 108, 109, 119, 120, 130, 131, 141, 142, 152, 153 };
            var all = GetComponentsInChildren<Transform>(true);
            clothBones = new Transform[ids.Length];
            clothRest = new Quaternion[ids.Length];
            clothAxes = new Vector3[ids.Length];
            for (int i = 0; i < ids.Length; i++)
            {
                Transform bone = Array.Find(all, t => t.name == "Bone_" + ids[i].ToString("D3"));
                clothBones[i] = bone;
                if (!bone) continue;
                clothRest[i] = bone.localRotation;
                clothAxes[i] = bone.InverseTransformDirection(transform.right).normalized;
            }
            // Long back hair chains; facial and head bones remain untouched.
            int[] hairIds = { 175, 176, 177, 181, 182, 183, 187, 188, 189,
                              217, 218, 219, 226, 227, 228 };
            hairBones = new Transform[hairIds.Length];
            hairRest = new Quaternion[hairIds.Length];
            hairAxes = new Vector3[hairIds.Length];
            for (int i = 0; i < hairIds.Length; i++)
            {
                var bone = Array.Find(all, t => t.name == "Bone_" + hairIds[i].ToString("D3"));
                hairBones[i] = bone;
                if (!bone) continue;
                hairRest[i] = bone.localRotation;
                hairAxes[i] = bone.InverseTransformDirection(transform.right).normalized;
            }
            windBlend = 0f;
        }
        void ApplyClothWind(float dt)
        {
            if (clothBones == null) return;
            float speed = motor ? motor.PlanarSpeed : 0f;
            float sprint = motor ? Mathf.InverseLerp(motor.walkSpeed, motor.sprintSpeed, speed) : 0f;
            windBlend = Mathf.Lerp(windBlend, sprint, 1f - Mathf.Exp(-3f * dt));
            for (int i = 0; i < clothBones.Length; i++)
            {
                if (!clothBones[i]) continue;
                float chain = i / 2;
                float wave = Mathf.Sin(clock * (1.3f + .5f * windBlend) + chain * .55f - (i % 2) * .55f);
                float gust = Mathf.Sin(clock * .43f + chain * .3f);
                float angle = wave * (1.4f + 3.6f * windBlend) + gust * .8f + 2f * windBlend;
                clothBones[i].localRotation = clothRest[i] * Quaternion.AngleAxis(angle, clothAxes[i]);
            }
            if (hairBones == null) return;
            for (int i = 0; i < hairBones.Length; i++)
            {
                if (!hairBones[i]) continue;
                float chain = i / 3;
                float segment = i % 3;
                float wave = Mathf.Sin(clock * (1.25f + .8f * windBlend) + chain * .8f - segment * .65f);
                float gust = Mathf.Sin(clock * .55f + chain * .4f);
                float angle = wave * (.9f + 3.2f * windBlend) + gust * .7f + 2.5f * windBlend;
                hairBones[i].localRotation = hairRest[i] * Quaternion.AngleAxis(angle, hairAxes[i]);
            }
        }
        public string MotionState { get; private set; } = "Idle";
        float runBlend, airBlend, landing;
        float lastYaw, turnLean;
        bool wasGrounded = true;
        void LateUpdate()
        {
            if (!movementRoot || joints == null || joints.Length == 0) return;
            float dt = Mathf.Max(Time.deltaTime, .0001f);
            currentSpeed = motor ? motor.PlanarSpeed : new Vector2(
                movementRoot.position.x-previousPosition.x,movementRoot.position.z-previousPosition.z).magnitude/dt;
            previousPosition=movementRoot.position;
            float target = Mathf.Clamp01(currentSpeed / Mathf.Max(motor ? motor.walkSpeed : 1.2f,.1f));
            float run = Mathf.InverseLerp(motor ? motor.walkSpeed : 1.2f,motor ? motor.sprintSpeed : 4f,currentSpeed);
            bool grounded = !motor || motor.Grounded;
            if (grounded && !wasGrounded) landing=.9f;
            wasGrounded=grounded;
            landing=Mathf.MoveTowards(landing,0f,dt*4f);
            movement=Mathf.Lerp(movement,target,1f-Mathf.Exp(-10f*dt));
            runBlend=Mathf.Lerp(runBlend,run,1f-Mathf.Exp(-8f*dt));
            airBlend=Mathf.Lerp(airBlend,grounded ? 0f : 1f,1f-Mathf.Exp(-12f*dt));
            clock+=dt;
            // Match cadence to the locomotion speed and ease into a turn instead of snapping.
            float yaw = transform.parent ? transform.parent.eulerAngles.y : transform.eulerAngles.y;
            float yawRate = Mathf.DeltaAngle(lastYaw, yaw) / dt;
            lastYaw = yaw;
            float targetLean = Mathf.Clamp(-yawRate * .025f, -7f, 7f) * movement * (1f-airBlend);
            turnLean = Mathf.Lerp(turnLean, targetLean, 1f-Mathf.Exp(-8f*dt));
            motionPhase+=dt*Mathf.Lerp(6.5f,10.5f,runBlend)*Mathf.Lerp(.2f,1f,movement);
            MotionState=!grounded ? (motor.VerticalSpeed>0f ? "Jump" : "Fall") :
                currentSpeed<.08f ? "Idle" : run>.65f ? "Run" : run>.15f ? "Jog" : "Walk";
            ApplyLocomotion(clock,motionPhase,movement,runBlend,airBlend,motor ? motor.VerticalSpeed : 0f,landing);
            ApplyClothWind(dt);
        }
        // Kept for the existing pose-preview and skin-validation editor tools.
        public void ApplyPose(float time,float phase,float amount,bool flying)
        { ApplyLocomotion(time,phase,amount,0f,flying ? 1f : 0f,0f,0f); }

        public void ApplyLocomotion(float time,float phase,float amount,float run,float air,float vertical,float land)
        {
            if(joints==null || joints.Length<14) return;
            float wave=Mathf.Sin(phase);
            float breath=Mathf.Sin(time*1.8f);
            float sway=Mathf.Sin(time*.75f);
            float grounded=1f-air;
            float stride=Mathf.Lerp(walkingAmplitude,37f,run)*amount*grounded;
            float knee=Mathf.Lerp(32f,58f,run)*amount*grounded;
            float arms=Mathf.Lerp(19f,34f,run)*amount*grounded;
            // Hold the planted leg longer, while the other foot recovers briskly.
            float recoveryL=Mathf.Pow(Mathf.Max(0f,-wave), 1.15f);
            float recoveryR=Mathf.Pow(Mathf.Max(0f,wave), 1.15f);
            float counterTwist=Mathf.Sin(phase+.22f)*amount*grounded;
            float idle=1f-amount;
            transform.localPosition=restPosition+Vector3.up*(
                breath*breathingAmplitude*.55f*idle+Mathf.Abs(wave)*Mathf.Lerp(.010f,.018f,run)*amount*grounded-.065f*land);
            // The stylized run leans forward, recovers upright in air, and banks gently into turns.
            transform.localRotation=restRotation*Quaternion.Euler(5f*run*amount+4f*air, counterTwist*1.2f, sway*.3f*idle+turnLean*.6f);
            foreach(var j in joints) if(j.bone) j.bone.localRotation=j.rest;
            Rotate(0,breath*.7f+2f*run*amount+5f*land,counterTwist*1.2f+sway*.3f*idle);
            Rotate(1,-breath*.12f-2f*run*amount,-sway*.1f*idle-counterTwist*.2f);
            Rotate(2,-wave*arms-15f*air,-joints[2].side*(35f-breath*.8f-7f*air));
            Rotate(3,wave*arms-15f*air,-joints[3].side*(35f-breath*.8f-7f*air));
            Rotate(4,-8f-38f*run*amount-20f*air-recoveryR*amount*12f,0f);
            Rotate(5,-8f-38f*run*amount-20f*air-recoveryL*amount*12f,0f);
            if (fingers != null)
                foreach (var finger in fingers)
                    if (finger.bone) finger.bone.localRotation = finger.rest *
                        Quaternion.AngleAxis(finger.curlDegrees * run * amount, finger.curlAxis);
            float tuck=air*(vertical>0f ? 23f : 10f);
            for(int i=6;i<=10;i+=4)
            {
                Rotate(i,wave*stride-tuck,0f);
                Rotate(i+1,-wave*stride-tuck*.65f,0f);
                Rotate(i+2,recoveryL*knee+tuck*1.5f+22f*land,0f);
                Rotate(i+3,recoveryR*knee+tuck+22f*land,0f);
            }
        }
        void Rotate(int index, float pitch, float roll)
        {
            if (index >= joints.Length) return;
            var j = joints[index];
            if (j.bone) j.bone.localRotation = j.rest *
                Quaternion.AngleAxis(roll, j.rollAxis) * Quaternion.AngleAxis(pitch, j.pitchAxis);
        }
        void OnDisable()
        {
            if (joints != null) foreach (var j in joints)
                if (j.bone) j.bone.localRotation = j.rest;
            if (fingers != null) foreach (var finger in fingers)
                if (finger.bone) finger.bone.localRotation = finger.rest;
            if (clothBones != null) for (int i = 0; i < clothBones.Length; i++)
                if (clothBones[i]) clothBones[i].localRotation = clothRest[i];
            if (hairBones != null) for (int i = 0; i < hairBones.Length; i++)
                if (hairBones[i]) hairBones[i].localRotation = hairRest[i];
            transform.localPosition = restPosition;
            transform.localRotation = restRotation;
        }
    }
}

