package com.microsoft.Malmo.Mixins;

import com.microsoft.Malmo.Access.IMixinMixinVec3drotatePitchLidar;

import net.minecraft.util.math.Vec3d;
import net.minecraft.util.math.MathHelper;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;

@Mixin(Vec3d.class)
public abstract class MixinVec3d implements IMixinMixinVec3drotatePitchLidar{

    @Shadow public double xCoord;
    @Shadow public double yCoord;
    @Shadow public double zCoord;

    @Override
    public Vec3d rotatePitchLidar(float pitch)
    {   
        float pitch_radian;
        float pitch_degree = pitch * (float)180.0 / (float)Math.PI;
        double x = this.xCoord;
        double z = this.zCoord;
        float origin_pitch_degree = (float)MathHelper.atan2(this.yCoord, MathHelper.sqrt(x*x + z*z)) * (float)180.0 / (float)Math.PI;
        if (origin_pitch_degree + pitch_degree > 89){
            pitch_radian = 89 / (float)180.0 * (float)Math.PI;
        } else if (origin_pitch_degree + pitch_degree < -89){
            pitch_radian = -89 / (float)180.0 * (float)Math.PI;
        } else {
            pitch_radian = (origin_pitch_degree + pitch_degree) / (float)180.0 * (float)Math.PI;
        }
        float f = MathHelper.sin(pitch_radian)/MathHelper.cos(pitch_radian);
        double y = (double)f * MathHelper.sqrt(x*x + z*z);
        double ratio = 1.0 / MathHelper.sqrt(y*y + x*x + z*z);
        double d0 = ratio * x;
        double d1 = ratio * y;
        double d2 = ratio * z;
        return new Vec3d(d0, d1, d2);
    }
}
