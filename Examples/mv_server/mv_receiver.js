import {
  get_forward_mvs,
} from "../free-for-all/helpers.mjs";

let zmq;
let zreq;

export function setup(args)
{
  args.features = [ "mv" ];

  zmq = new ZMQ();
  zreq = zmq.socket(ZMQ.ZMQ_REQ);
  zreq.connect("tcp://localhost:5556");
}

let request_sent = false;
export function glitch_frame(frame, stream)
{
  const fwd_mvs = get_forward_mvs(frame, "truncate");
  // bail out if we have no motion vectors
  if ( !fwd_mvs )
    return;

  if ( !request_sent )
  {
    const data = new Uint8FFArray(1); // the content doesn't matter
    zreq.send(data, ZMQ.ZMQ_DONTWAIT);
    request_sent = true;
  }

  {
    const data = zreq.recv(zreq, ZMQ.ZMQ_DONTWAIT);
    if ( true ) {
      console.log(`received ${data.length} bytes`);
      fwd_mvs.assign(new MV2DArray(data));
      request_sent = false;
    }
  }
}
