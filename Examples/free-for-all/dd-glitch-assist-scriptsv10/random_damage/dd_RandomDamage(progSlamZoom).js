// dd_RandomDamage(progSlamZoom).js
// progressive SlamZoom x and y components of mv if threshold met for frame

let threshold = 95;

var ZOOM = 0;
var doZOOM = 0;
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
            ZOOM = 0;
        }
    }
    // only do the glitch if our random number crosses the threshold
    if(TRIGGERED > 0 & frameCount <= nFrames){
        frameCount++;
        ZOOM+= 10

        var do_dir = Math.random() * 100;
        if(do_dir > 50){
            doZOOM = 0 - ZOOM;
        }else{
            doZOOM = ZOOM
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
            mv[0] = ((M_W - j) / 10) * doZOOM;
            mv[1] = ((M_H - i) / 10) * doZOOM;
        });
    }else{
        TRIGGERED = 0;
    }
}
