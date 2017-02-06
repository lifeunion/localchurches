$(document).ready(function() {
	'use strict';
	
	/**
	 * Checkbox & radio inputs
	 */
	$('input[type=checkbox], input[type=radio]').ezMark();

	/**
	 * Map Leaflet Contact
	 */
	if ($('#map-contact').length) {
		var map = L.map('map-contact', {
			zoom: 12,
			maxZoom: 20,
			center: [40.761077, -73.88]
		});			

		map.scrollWheelZoom.disable();
		var access_token = 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpandmbXliNDBjZWd2M2x6bDk3c2ZtOTkifQ._QA7i5Mpkd_m30IGElHziw';

		L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + access_token, {		
			scrollWheelZoom: false,		
			id: 'mapbox.streets',
			attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Terms &amp; Feedback</a>'
		}).addTo(map);	
		
		var icon = L.divIcon({
			html: '<i class="fa fa-suitcase"></i>',
            iconSize: [36, 36],
            iconAnchor: [36, 36],
            popupAnchor: [-20, -42]
        });

		var marker = L.marker([40.761077, -73.88], {
			icon: icon
		}).addTo(map);	
	}

	/**
	 * Map Leaflet
	 */
	if ($('#map-leaflet').length) {
		var map = L.map('map-leaflet', {
			zoom: 12,
			maxZoom: 20,
			center: [40.761077, -73.88]
		});	

		var access_token = 'pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpandmbXliNDBjZWd2M2x6bDk3c2ZtOTkifQ._QA7i5Mpkd_m30IGElHziw';
 		var marker_cluster = L.markerClusterGroup();		

		map.scrollWheelZoom.disable();

		L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=' + access_token, {		
			scrollWheelZoom: false,		
			id: 'mapbox.streets',
			attribution: '<a href="http://www.mapbox.com/about/maps/" target="_blank">Terms &amp; Feedback</a>'
		}).addTo(map);

		$.ajax('assets/data/markers.json', {
			success: function(markers) {
				$.each(markers, function(index, value) {
			        var icon = L.divIcon({
			        	html: value.icon,
			            iconSize:     [36, 36],
			            iconAnchor:   [36, 36],
			            popupAnchor:  [-20, -42]
			        });

					var marker = L.marker(value.center, {
						icon: icon
					}).addTo(map);		

	                marker.bindPopup(
	                    '<div class="listing-window-image-wrapper">' +
	                        '<a href="properties-detail-standard.html">' +
	                            '<div class="listing-window-image" style="background-image: url(' + value.image + ');"></div>' +
	                            '<div class="listing-window-content">' +
	                                '<div class="info">' +
	                                    '<h2>' + value.title + '</h2>' +
	                                    '<h3>' + value.price + '</h3>' +
	                                '</div>' +
	                            '</div>' +
	                        '</a>' +
	                    '</div>'
	                );

					marker_cluster.addLayer(marker);
				});

				map.addLayer(marker_cluster);
			}
		});
	}

	/**
	 * Google Map
	 */
	if ($('#map-google').length) {
		$.ajax('assets/data/markers.json', {
			success: function(values) {
				var markers = [];
				var infos = [];

				$.each(values, function(index, value) {
	                var content = '<div id="' + value.id + '" class="map-popup-content-wrapper"><div class="map-popup-content"><div class="listing-window-image-wrapper">' +
	                        '<a href="properties-detail-standard.html">' +
	                            '<div class="listing-window-image" style="background-image: url(' + value.image + ');"></div>' +
	                            '<div class="listing-window-content">' +
	                                '<div class="info">' +
	                                    '<h2>' + value.title + '</h2>' +
	                                    '<h3>' + value.price + '</h3>' +
	                                '</div>' +
	                            '</div>' +
	                        '</a>' +
	                    '</div></div><i class="fa fa-close close"></i></div>' +
	                    '<div class="map-marker">' + value.icon + '</div>';

					markers.push({
						latLng: value.center, 
						data: value.id,			
						options: {									
							content: content,
							offset: {
                				x: -18,
                				y: -42
              				}							
						}
					});
				});

				$('#map-google').gmap3({		
					map: {									
						options:{
							styles: [{"featureType":"landscape","elementType":"all","stylers":[{"hue":"#FFBB00"},{"saturation":43.400000000000006},{"lightness":37.599999999999994},{"gamma":1}]},{"featureType":"poi","elementType":"all","stylers":[{"hue":"#00FF6A"},{"saturation":-1.0989010989011234},{"lightness":11.200000000000017},{"gamma":1}]},{"featureType":"road.highway","elementType":"all","stylers":[{"hue":"#FFC200"},{"saturation":-61.8},{"lightness":45.599999999999994},{"gamma":1}]},{"featureType":"road.arterial","elementType":"all","stylers":[{"hue":"#FF0300"},{"saturation":-100},{"lightness":51.19999999999999},{"gamma":1}]},{"featureType":"road.local","elementType":"all","stylers":[{"hue":"#FF0300"},{"saturation":-100},{"lightness":52},{"gamma":1}]},{"featureType":"water","elementType":"all","stylers":[{"hue":"#0078FF"},{"saturation":-13.200000000000003},{"lightness":2.4000000000000057},{"gamma":1}]}],
							center:[40.761077, -73.88],
							scrollwheel: false,
							zoom: 12
						}
					},
					marker: {
						cluster: {
      						radius: 100,
      					}
					},
					overlay: {
						values: markers,
						events: {
							click: function(marker, event, context) {															
								$('.map-popup-content-wrapper').css('display', 'none');

								if ($(event[0].target).hasClass('close')) {
									$('#' + context.data).css('display', 'none');
								} else {
									$('#' + context.data).css('display', 'block');
								}
							}
						}
					}
				});					
			}		
		});
	}

	/**
	 * Properties Carousel
	 */
	 $('.listing-carousel').owlCarousel({
	 	items: 4,
	 	margin: 30,
	 	nav: true,
	 	navText: ['<i class="fa fa-chevron-left"></i>', '<i class="fa fa-chevron-right"></i>'],
	 	responsive: {
	 		0: {
	 			items: 1
	 		},
	 		540: {
	 			items: 2
	 		},	
	 		766: {
	 			items: 2
	 		},
	 		990: {
	 			items: 3
	 		},
	 		1200: {
	 			items: 4
	 		}	 		
	 	}
	 });

	/**
	 * Cover carousel
	 */
	 $('.cover-carousel').owlCarousel({
	 	items: 1,
	 	nav: true,
	 	navText: ['<img src="assets/img/lnr-chevron-left.svg" alt="">', '<img src="assets/img/lnr-chevron-right.svg" alt="">']
	 });

	/**
	 * Image gallery
	 */
	 $('.gallery').owlCarousel({
	 	autoplay: 3000,
	 	items: 1,
	 	nav: true,
	 	navText: ['<i class="fa fa-chevron-left"></i>', '<i class="fa fa-chevron-right"></i>']
	 });

	/**
	 * Customizer
	 */	 
	$('.customizer-title').on('click', function() {		
		$('.customizer').toggleClass('open');
	});

	$('.customizer a').click('click', function(e) {
		e.preventDefault();

		var cssFile = $(this).attr('href');
		$('#css-primary').attr('href', cssFile);
	});

	/**
	 * Charts
     */
    if ($('.ct-chart-1').length) {
		var data = {
			labels: ['Jan', 'Feb', 'Mar', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
			series: [
				[5, 4, 3, 7, 5, 10, 3, 4, 8, 10, 6, 8],
				[3, 2, 9, 5, 4, 6, 4, 6, 7, 8, 7, 4]
			]
		};

		var options = {
			seriesBarDistance: 15
		};

		var responsiveOptions = [
			['screen and (min-width: 641px) and (max-width: 1024px)', {
				seriesBarDistance: 10,
				axisX: {
					labelInterpolationFnc: function (value) {
						return value;
					}
				}
			}],
			['screen and (max-width: 640px)', {
				seriesBarDistance: 5,
				axisX: {
					labelInterpolationFnc: function (value) {
						return value[0];
					}
				}
			}]
		];

		new Chartist.Bar('.ct-chart-1', data, options, responsiveOptions);
	}

	/**
	 * Charts
	 */
	if ($('.ct-chart-2').length) {
		new Chartist.Line('.ct-chart-2', {
			labels: [1, 2, 3, 4, 5, 6, 7, 8],
			series: [
				[1, 2, 3, 1, -2, 0, 1, 0],
				[-2, -1, -2, -1, -2.5, -1, -2, -1],
				[0, 0, 0, 1, 2, 2.5, 2, 1],
				[2.5, 2, 1, 0.5, 1, 0.5, -1, -2.5]
			]
		}, {
			high: 3,
			low: -3,
			showArea: true,
			showLine: false,
			showPoint: false,
			fullWidth: true,
			axisX: {
				showLabel: false,
				showGrid: false
			}
		});
	}

	/**
	 * Charts
	 */
	if ($('.ct-chart-3').length) {
		new Chartist.Bar('.ct-chart-3', {
			labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
			series: [
				[5, 4, 3, 7, 5, 10, 3],
				[3, 2, 9, 5, 4, 6, 4]
			]
		}, {
			seriesBarDistance: 10,
			reverseData: true,
			horizontalBars: true,
			axisY: {
				offset: 70
			}
		});
	}

	/**
	 * Charts
	 */
	if ($('.ct-chart-4').length) {
		var times = function(n) {
			return Array.apply(null, new Array(n));
		};

		var data = times(52).map(Math.random).reduce(function(data, rnd, index) {
			data.labels.push(index + 1);
			data.series.forEach(function(series) {
				series.push(Math.random() * 100)
			});

			return data;
		}, {
			labels: [],
			series: times(4).map(function() { return new Array() })
		});

		var options = {
			showLine: false,
			axisX: {
				labelInterpolationFnc: function(value, index) {
					return index % 13 === 0 ? 'W' + value : null;
				}
			}
		};

		var responsiveOptions = [
			['screen and (min-width: 640px)', {
				axisX: {
					labelInterpolationFnc: function(value, index) {
						return index % 4 === 0 ? 'W' + value : null;
					}
				}
			}]
		];

		new Chartist.Line('.ct-chart-4', data, options, responsiveOptions);
	}
});