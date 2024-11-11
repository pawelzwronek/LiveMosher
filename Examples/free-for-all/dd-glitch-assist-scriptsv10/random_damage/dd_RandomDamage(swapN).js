// dd_RandomDamage(swapN).js
// swap x and y component of mv for n framesif threshold met for frame

let threshold = 95;
var TRIGGERED = 0;
var nFrames = 5;
var frameCount = 0;

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
            frameCount = 0;
        }
    }
    // only do the glitch if our random number crosses the threshold
    if(TRIGGERED > 0 & frameCount <= nFrames){
        frameCount++;

        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        fwd_mvs.swap_hv();
    }else{
        TRIGGERED = 0;
    }
}
