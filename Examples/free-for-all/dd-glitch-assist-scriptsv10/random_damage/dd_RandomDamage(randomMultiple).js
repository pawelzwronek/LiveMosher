// dd_RandomDamage(randomMultiple).js
// radom multiplies x and y components of mv if threshold met for frame

let threshold = 95;
let multiplier = 10;

export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    var do_or_not = Math.random() * 100;
    // only do the glitch if our random number crosses the threshold
    if(do_or_not > threshold){
        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        fwd_mvs.forEach((mv) => {
            mv[0] += Math.random() * multiplier;
            mv[1] += Math.random() * multiplier;
        });
    }
}
