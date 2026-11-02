using UnityEngine;
namespace Game.ThirdPerson
{
    [RequireComponent(typeof(Animator))]
    public sealed class FbxLocomotion : MonoBehaviour
    {
        public ThirdPersonMotor motor;
        Animator animator;
        Transform[] source, auxiliary;
        void Awake()
        {
            animator = GetComponent<Animator>();
            if (!motor) motor = GetComponentInParent<ThirdPersonMotor>();
            var all = GetComponentsInChildren<Transform>(true);
            string[] names = { "Thigh_L", "Shin_L", "Foot_L", "Thigh_R", "Shin_R", "Foot_R" };
            string[] copies = { "ThighAux_L", "ShinAux_L", "Bone_015", "ThighAux_R", "ShinAux_R", "Bone_025" };
            source = new Transform[names.Length]; auxiliary = new Transform[names.Length];
            foreach (var t in all)
                for (int i = 0; i < names.Length; i++)
                { if (t.name == names[i]) source[i] = t; if (t.name == copies[i]) auxiliary[i] = t; }
        }
        void Update()
        {
            if (!motor || !animator) return;
            animator.SetBool("Moving", motor.PlanarSpeed > .08f && motor.Grounded);
            animator.speed = motor.Sprinting ? 1.5f : 1f;
        }
        void LateUpdate()
        {
            if (source == null) return;
            for (int i = 0; i < source.Length; i++)
                if (source[i] && auxiliary[i]) auxiliary[i].localRotation = source[i].localRotation;
        }
    }
}
