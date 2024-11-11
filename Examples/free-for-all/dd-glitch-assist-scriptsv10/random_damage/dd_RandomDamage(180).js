// dd_RandomDamage(180).js
// randomly rotate by 180 x and y components of mv if threshold met for frame

let threshold = 95;
var ZOOM = 100;

export function setup(args)
{
    args.features = [ "mv" ];
}

export function glitch_frame(frame)
{
    var do_or_not = Math.random() * 100;
    // only do the glitch if our random number crosses the threshold
    if(do_or_not > threshold){
        ZOOM = Math.random() * 100;
        var do_dir = Math.random() * 100;
        if(do_dir > 50){
            ZOOM = 0 - ZOOM;
        }
        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        // note that we perform a deep copy of the clean motion
        // vector values before modifying them.
        let deep_copy = fwd_mvs.dup();


        // clear horizontal element of all motion vectors
        for ( let i = 0; i < fwd_mvs.length; i++ )
        {
            // loop through all rows
            let row = fwd_mvs[i];
            var row2 = deep_copy[(fwd_mvs.length-1)-i];
            for ( let j = 0; j < row.length; j++ )
            {
                // loop through all macroblocks
                let mv = row[j];
                var mv2 = row2[(row.length - 1) - j];
                mv[0] = -mv2[0];
                mv[1] = -mv2[1];
            }
        }
    }
}
