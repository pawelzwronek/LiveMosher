// dd_RandomDamage(wave).js
// sin/cos x and y components of mv if threshold met for frame

let threshold = 95;
var nFrames = 5;
var TRIGGERED = 0;
var count = 0;

export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    var do_or_not = Math.random() * 100;
    // only do the glitch if our random number crosses the threshold
    if(do_or_not > threshold | TRIGGERED == 1){
        if(TRIGGERED == 0){
            TRIGGERED = 1;
            count = 0;
        }
        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        const M_H = fwd_mvs.height / 2;
        const M_W = fwd_mvs.width  / 2;

        fwd_mvs.forEach((mv, i, j) => {
            mv[0] *= Math.sin(i/M_W*Math.PI*2);
            mv[1] *= Math.cos(j/M_H*Math.PI*2);
        });

        count++;
        if(count >= nFrames){
            TRIGGERED = 0;
        }
    }
}
