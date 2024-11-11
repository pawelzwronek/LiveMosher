// dd_RandomDamage(displaceY).js
// displace y component of mv if threshold met for frame

let threshold = 95;

var DISPLACE = 0;
var MAGNITUDE = 100;

export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    var do_or_not = Math.random() * 100;
    // only do the glitch if our random number crosses the threshold
    if(do_or_not > threshold){
        DISPLACE = Math.random() * MAGNITUDE;
        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        fwd_mvs.add_v(DISPLACE);
    }
}
