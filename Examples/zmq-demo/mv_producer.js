import * as zmq from "zmq";

import {
  get_forward_mvs,
} from "../free-for-all/helpers.mjs";

let zpush;

export function setup(args)
{
  args.features = [ "mv" ];

  const ctx = new zmq.Context();
  zpush = ctx.socket(zmq.PUSH);
  zpush.connect("tcp://localhost:5555");

  // (new ZMQ()).socket(ZMQ.ZMQ_PUSH);
}

export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  const data = fwd_mvs.serialize();
  zpush.send(data, zmq.DONTWAIT);
}
