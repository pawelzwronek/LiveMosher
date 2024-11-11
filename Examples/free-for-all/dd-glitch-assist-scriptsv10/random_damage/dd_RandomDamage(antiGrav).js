// dd_RandomDamage(antiGrav).js
// anitgravityify if threshold met for frame

let threshold = 98;
// global variable holding forward motion vectors from previous frames
var old_mvs = [ ];
// a variable for gravity
var rt = 0;
var gravity = 0
var orig_gravity = 5;
var TRIGGERED = 0;
var frameCount = 10;
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
            gravity = orig_gravity;
            TRIGGERED = 1;
            rt = 0;
        }
        // bail out if we have no forward motion vectors
        const fwd_mvs = frame.mv?.forward;
        if ( !fwd_mvs )
            return;

        // set motion vector overflow behaviour in ffedit to "truncate"
        frame.mv.overflow = "truncate";

        // buffer first set of vectors. . .
        if(rt == 0){
            let deep_copy = fwd_mvs.dup();
            // push to the end of array
            old_mvs[0] = (deep_copy);
            rt = 1;
        }

        // clear horizontal element of all motion vectors
        for ( let i = 0; i < fwd_mvs.length; i++ )
        {
            // loop through all rows
            let row = fwd_mvs[i];
            let old_row = old_mvs[0][i];
            for ( let j = 0; j < row.length; j++ )
            {
                // loop through all macroblocks
                let mv = row[j];
                let omv = old_row[j];
                mv[0] = mv[0];
                var nmv = mv[1];
                mv[1] = omv[1];
                omv[1] = nmv + omv[1] + gravity;
            }
        }
        count++;
        if(count >= frameCount){
            TRIGGERED = 0;
            count = 0;
        }
    }
}
