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
            motionPhase+=dt*Mathf.Lerp(6.5f,12.5f,runBlend)*Mathf.Lerp(.2f,1f,movement);
            MotionState=!grounded ? (motor.VerticalSpeed>0f ? "Jump" : "Fall") :
                currentSpeed<.08f ? "Idle" : run>.65f ? "Run" : run>.15f ? "Jog" : "Walk";
            ApplyLocomotion(clock,motionPhase,movement,runBlend,airBlend,motor ? motor.VerticalSpeed : 0f,landing);
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
            float stride=Mathf.Lerp(walkingAmplitude,42f,run)*amount*grounded;
            float knee=Mathf.Lerp(32f,68f,run)*amount*grounded;
            float arms=Mathf.Lerp(19f,46f,run)*amount*grounded;
            // Hold the planted leg longer, while the other foot recovers briskly.
            float recoveryL=Mathf.Pow(Mathf.Max(0f,-wave), .7f);
            float recoveryR=Mathf.Pow(Mathf.Max(0f,wave), .7f);
            float counterTwist=Mathf.Sin(phase+.22f)*amount*grounded;
            float idle=1f-amount;
            transform.localPosition=restPosition+Vector3.up*(
                breath*breathingAmplitude*.55f*idle+Mathf.Abs(wave)*Mathf.Lerp(.014f,.045f,run)*amount*grounded-.065f*land);
            // The stylized run leans forward, recovers upright in air, and banks gently into turns.
            transform.localRotation=restRotation*Quaternion.Euler(12f*run*amount+4f*air, counterTwist*2f, sway*.65f*idle+turnLean);
            foreach(var j in joints) if(j.bone) j.bone.localRotation=j.rest;
            Rotate(0,breath*1.1f+7f*run*amount+8f*land,counterTwist*3f+sway*.8f*idle);
            Rotate(1,-breath*.7f-4f*run*amount,-sway*.8f*idle-counterTwist);
            Rotate(2,-wave*arms-15f*air,-joints[2].side*(35f-breath*.8f-7f*air));
            Rotate(3,wave*arms-15f*air,-joints[3].side*(35f-breath*.8f-7f*air));
            Rotate(4,-8f-52f*run*amount-20f*air-recoveryR*amount*12f,0f);
            Rotate(5,-8f-52f*run*amount-20f*air-recoveryL*amount*12f,0f);
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
            transform.localPosition = restPosition;
            transform.localRotation = restRotation;
        }
    }
}

