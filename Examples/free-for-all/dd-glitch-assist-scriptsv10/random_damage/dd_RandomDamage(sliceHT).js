// dd_RandomDamage(sliceHT).js
// disrupt top of frame if threshold met

let threshold = 95;

var DISPLACE = 0;
var MAGNITUDE = 500;

export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    var do_or_not = Math.random() * 100;
    // only do the glitch if our random number crosses the threshold
    if(do_or_not > threshold){
        DISPLACE = (Math.random() * MAGNITUDE) - (MAGNITUDE*0.5);
        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        const M_H = fwd_mvs.height / 2;
        const M_W = fwd_mvs.width  / 2;

        fwd_mvs.forEach((mv, i, j) => {
            if (i <= M_H)
                mv[0] += DISPLACE;
        });
    }
}
