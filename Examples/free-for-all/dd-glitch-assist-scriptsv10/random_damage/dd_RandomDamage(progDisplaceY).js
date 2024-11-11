// dd_RandomDamage(progDisplaceY).js
// progressive displace y components of mv if threshold met for frame

let threshold = 95;



var TRIGGERED = 0;
var nFrames = 5;
var frameCount = 0;
var DISPLACE = 0;
var doDISPLACE = 0;
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
            frameCount = 0;
            DISPLACE = Math.random() * MAGNITUDE;
            var do_dir = Math.random() * 100;
            if(do_dir > 50){
                DISPLACE = 0 - DISPLACE;
            }else{
            }
            doDISPLACE = 0;
        }
    }
    // only do the glitch if our random number crosses the threshold
    if(TRIGGERED > 0 & frameCount <= nFrames){
        frameCount++;
        doDISPLACE += DISPLACE;

        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        fwd_mvs.add_v(doDISPLACE);
    }else{
        TRIGGERED = 0;
    }
}
