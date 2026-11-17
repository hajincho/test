float2 p = float2(UV.x * 3.0, UV.y);
float3 ink = float3(0.80, 0.96, 1.0);
float3 acc = float3(0.20, 0.72, 1.0);
float3 warn = float3(1.0, 0.45, 0.12);
float ammoI = clamp(floor(Ammo + 0.5), 0.0, 99.0);
float resI = clamp(floor(Reserve + 0.5), 0.0, 999.0);
float low = (ammoI <= 5.0) ? 1.0 : 0.0;
float3 mainc = lerp(ink, warn, low);
float aa = 0.006;
// plate: rectangle with the top-left and bottom-right corners cut
float2 dq = abs(p - float2(1.5, 0.5)) - float2(1.48, 0.48);
float dBox = -max(dq.x, dq.y);
float dC1 = (p.x + p.y - 0.30) * 0.7071;
float dC2 = ((3.0 - p.x) + (1.0 - p.y) - 0.30) * 0.7071;
float di = min(dBox, min(dC1, dC2));
float fill = smoothstep(0.0, aa, di);
float edge = fill * (1.0 - smoothstep(0.012, 0.012 + aa, di));
float cutE = fill * (1.0 - smoothstep(0.030, 0.030 + aa, min(dC1, dC2)));
float3 col = float3(0.015, 0.04, 0.075);
float alpha = fill * 0.62;
col = lerp(col, acc, edge); alpha = max(alpha, edge * 0.95);
col = lerp(col, ink, cutE); alpha = max(alpha, cutE);
// divider between weapon and counters
float dv = (1.0 - smoothstep(0.004, 0.004 + aa, abs(p.x - 1.47))) * step(0.17, p.y) * step(p.y, 0.74);
col = lerp(col, acc, dv * 0.6); alpha = max(alpha, dv * 0.55);
// weapon silhouette (our own M4 model)
float su = (p.x - 0.14) / 1.27; float sv = (p.y - 0.325) / (1.27 / 3.8398);
float insd = step(0.0, su) * step(su, 1.0) * step(0.0, sv) * step(sv, 1.0);
float4 tx = (Weapon > 0.5) ? Texture2DSample(Tex2, Tex2Sampler, float2(saturate(su), saturate(sv))) : Texture2DSample(Tex, TexSampler, float2(saturate(su), saturate(sv)));
float sa = tx.a * insd;
col = lerp(col, ink, sa); alpha = max(alpha, sa * 0.95);
// round pips: 20 bars (magazine capacity 20), filled = rounds in the magazine; while reloading a light runs along them
for (int i = 0; i < 20; i++)
{
    float x0 = 0.17 + i * 0.132;
    float m = step(x0, p.x) * step(p.x, x0 + 0.090) * step(0.855, p.y) * step(p.y, 0.915);
    float lit = ((i + 0.5) * (MagSize / 20.0) < Ammo) ? 1.0 : 0.0;
    // reloading: the pips fill from empty to full in step with the reload time (ReloadP 0..1 = elapsed / reload duration), the pip being filled fades in
    if (Reload > 0.5) lit = saturate(ReloadP * 20.0 - i);
    float3 pc = lerp(float3(0.16, 0.26, 0.36), (Reload > 0.5) ? ink : mainc, lit);
    col = lerp(col, pc, m); alpha = max(alpha, m * lerp(0.45, 1.0, lit));
}
// seven-segment digits (slanted): ammo 2 digits big, reserve 3 digits small; unlit segments stay as a faint ghost
float ox[5] = {1.55, 1.81, 2.27, 2.42, 2.57};
float oy[5] = {0.24, 0.24, 0.40, 0.40, 0.40};
float dw[5] = {0.19, 0.19, 0.10, 0.10, 0.10};
float dh[5] = {0.36, 0.36, 0.20, 0.20, 0.20};
float dt[5] = {0.042, 0.042, 0.024, 0.024, 0.024};
float vals[5];
vals[0] = floor(ammoI / 10.0); vals[1] = fmod(ammoI, 10.0);
vals[2] = floor(resI / 100.0); vals[3] = fmod(floor(resI / 10.0), 10.0); vals[4] = fmod(resI, 10.0);
float blank[5];
blank[0] = (ammoI < 10.0) ? 1.0 : 0.0; blank[1] = 0.0;
blank[2] = (resI < 100.0) ? 1.0 : 0.0; blank[3] = (resI < 10.0) ? 1.0 : 0.0; blank[4] = 0.0;
int pat[10] = {63, 6, 91, 79, 102, 109, 125, 7, 127, 111};
for (int k = 0; k < 5; k++)
{
    float w = dw[k]; float h = dh[k]; float t = dt[k]; float g = t * 0.35;
    float2 lp = p - float2(ox[k], oy[k]);
    lp.x += (h * 0.5 - lp.y) * 0.0;
    float4 sg[7];
    sg[0] = float4(t * 0.8, 0.0, w - t * 0.8, t);
    sg[1] = float4(w - t, g + t * 0.5, w, h * 0.5 - g);
    sg[2] = float4(w - t, h * 0.5 + g, w, h - t * 0.5 - g);
    sg[3] = float4(t * 0.8, h - t, w - t * 0.8, h);
    sg[4] = float4(0.0, h * 0.5 + g, t, h - t * 0.5 - g);
    sg[5] = float4(0.0, g + t * 0.5, t, h * 0.5 - g);
    sg[6] = float4(t * 0.8, h * 0.5 - t * 0.5, w - t * 0.8, h * 0.5 + t * 0.5);
    int bits = pat[(int)vals[k]];
    for (int s = 0; s < 7; s++)
    {
        float m = step(sg[s].x, lp.x) * step(lp.x, sg[s].z) * step(sg[s].y, lp.y) * step(lp.y, sg[s].w);
        float on = (((bits >> s) & 1) == 1 && blank[k] < 0.5) ? 1.0 : 0.0;
        float3 dc = (k >= 2) ? ink : mainc;   // only the magazine count turns orange when low
        col = lerp(col, dc, m * on); alpha = max(alpha, m * lerp(0.13, 1.0, on));
    }
}
// slash between magazine and reserve
float2 sa0 = float2(2.235, 0.40); float2 sb0 = float2(2.165, 0.62);
float2 pa = p - sa0; float2 ba = sb0 - sa0;
float hh = saturate(dot(pa, ba) / dot(ba, ba));
float dl = length(pa - ba * hh);
float sl = 1.0 - smoothstep(0.010, 0.010 + aa, dl);
col = lerp(col, acc, sl); alpha = max(alpha, sl);
return float4(col, alpha);