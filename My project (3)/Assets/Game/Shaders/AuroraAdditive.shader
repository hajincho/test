Shader "Game/AuroraAdditive"
{
    Properties
    {
        _UnlitColorMap("Aurora", 2D) = "white" {}
        [HDR] _UnlitColor("Tint", Color) = (1,1,1,1)
    }
    SubShader
    {
        Tags { "RenderPipeline"="HDRenderPipeline" "Queue"="Transparent" "RenderType"="Transparent" }
        Pass
        {
            Name "ForwardOnly"
            Tags { "LightMode"="ForwardOnly" }
            Blend One One
            ZWrite Off
            ZTest LEqual
            Cull Off
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/Common.hlsl"
            #include "Packages/com.unity.render-pipelines.high-definition/Runtime/ShaderLibrary/ShaderVariables.hlsl"
            #include "Packages/com.unity.render-pipelines.core/ShaderLibrary/SpaceTransforms.hlsl"
            TEXTURE2D(_UnlitColorMap);
            SAMPLER(sampler_UnlitColorMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _UnlitColor;
                float4 _UnlitColorMap_ST;
            CBUFFER_END
            struct Attributes { float3 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };
            Varyings Vert(Attributes input)
            {
                Varyings output;
                output.positionCS = TransformObjectToHClip(input.positionOS);
                output.uv = input.uv * _UnlitColorMap_ST.xy + _UnlitColorMap_ST.zw;
                return output;
            }
            float4 Frag(Varyings input) : SV_Target
            {
                float4 sampleColor = SAMPLE_TEXTURE2D(_UnlitColorMap, sampler_UnlitColorMap, input.uv);
                float alpha = saturate(sampleColor.a * _UnlitColor.a);
                return float4(max(0, sampleColor.rgb * _UnlitColor.rgb) * alpha, 0);
            }
            ENDHLSL
        }
    }
}
