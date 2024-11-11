// dd_RandomDamage(twitch).js
// stop x then stop y component of mv for n frames if threshold met for frame


let threshold = 95;
var TRIGGERED = 0;
var nFrames = 10;
var MAXFRAMES = 10;
var frameCount = 0;
var MAGNITUDE = 5;
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
            //nFrames = Math.random() * MAXFRAMES;
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

        const M_H = fwd_mvs.height / 2;
        const M_W = fwd_mvs.width  / 2;

        fwd_mvs.forEach((mv, i, j) => {
            if ( frameCount == 0 )
            {
                mv[0] *= MAGNITUDE;
                mv[1] = 0;
            }
            if ( frameCount == 1 )
            {
                mv[1] *= MAGNITUDE;
                mv[0] = 0;
            }
        });

        frameCount++;
    }else{
        TRIGGERED = 0;
    }
}
