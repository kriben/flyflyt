function lookup_location() {
  if (geo_position_js.init()) {
    geo_position_js.getCurrentPosition(get_closest_airport, show_error, { enableHighAccuracy : true });
  }
};

function get_closest_airport(loc) 
{ 
  window.location = "/closest?latitude=" + loc.coords.latitude + "&longitude=" + loc.coords.longitude;
};

function show_error() 
{
  alert("Unable to determine currect location.");
};
