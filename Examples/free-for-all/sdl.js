export class SDLInput
{
  constructor()
  {
    this.sdl = new SDL();
    this.events_axis = {};
    this.events_hat = {};
    this.events_button = {};
    this.lasthat = 0;
    this.log = false;
  }

  setup(arg)
  {
    // are we being called by fflive?
    if ( !this.sdl )
    {
      console.log("we are not being called by fflive.");
      return false;
    }

    const njoysticks = this.sdl.numJoysticks();
    console.log("number of joysticks: " + njoysticks);
    if ( njoysticks > 0 )
      this.sdl.joystickOpen(0);

    return true;
  }

  setlog(b)
  {
    this.log = b;
  }

  on_axis(v, func)
  {
    this.events_axis[v] = func;
  }

  on_hat(v, func)
  {
    this.events_hat[v] = func;
  }

  on_button(v, func)
  {
    this.events_button[v] = func;
  }

  SDL_Event(event)
  {
    if ( this.log )
      console.log(JSON.stringify(event));

    // event.type
    // event.timestamp

    if ( event.type === SDL.SDL_JOYAXISMOTION )
    {
      // event.which
      // event.axis
      // event.value
      const event_v = this.events_axis[event.axis];
      if ( event_v !== undefined )
        event_v(event.value);
    }
    else if ( event.type === SDL.SDL_JOYHATMOTION )
    {
      // event.which
      // event.hat
      // event.value
      const event_v = this.events_hat[event.hat];
      if ( event_v !== undefined )
        event_v(event.value);
    }
    else if ( event.type === SDL.SDL_JOYBUTTONDOWN
           || event.type === SDL.SDL_JOYBUTTONUP )
    {
      // event.which
      // event.button
      // event.state
      const event_v = this.events_button[event.button];
      if ( event_v !== undefined )
        event_v(event.state);
    }
  }

  parse_events()
  {
    while ( this.sdl )
    {
        const event = this.sdl.getEvent();
        if ( !event )
            break;
        this.SDL_Event(event);
    }
  }
}
