// dd_RandomDamage(stopXYSmash).js
// stop x and y component of mv for n frames if threshold met for frame
// then SMASH.

let threshold = 98;
var TRIGGERED = 0;
var nFrames = 10;
var MAXFRAMES = 10;
var frameCount = 0;
var MAGNITUDE = 100;
export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    var do_or_not = Math.random() * 100;
    if(do_or_not > threshold){
        if(TRIGGERED > 0){

        }else{
            TRIGGERED = 1;
            nFrames = Math.round((MAXFRAMES * 0.5) + (Math.random() * MAXFRAMES * 0.5));
            frameCount = 0;
        }
    }
    // only do the glitch if our random number crosses the threshold
    if(TRIGGERED > 0 & frameCount <= nFrames){

        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        if (frameCount == nFrames)
            fwd_mvs.mul(MAGNITUDE, MAGNITUDE);
        else
            fwd_mvs.assign(0, 0);

        frameCount++;
    }else{
        TRIGGERED = 0;
    }
}
