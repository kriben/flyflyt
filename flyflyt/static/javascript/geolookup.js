function lookup_location() {
   navigator.geolocation.getCurrentPosition(show_map, show_map_error, { enableHighAccuracy : true });
};

function show_map(loc) 
{ 
  window.location = "/closest?latitude=" + loc.coords.latitude + "&longitude=" + loc.coords.longitude;
};

function show_map_error() 
{
  alert("Unable to determine currect location.");
};