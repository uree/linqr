function addButton(p1){
    var button = '<input type="button" value="new button" />';
    return button;
}

function addMenu(){
    var checkbox = '<input type="checkbox" value="keep" class="keep" checked>keep</input><input type="button" value="correction" class="correction"/>';
    return checkbox;
}


function link2color(links) {
    var out = 'balls'
    for (var d = 0; d < links.length; d++) {
        if (links[d]['type'] == 'open_url') {
            var one = '<span class="open">&#9633;</span>'
            out += one

        } else if (links[d]['type'] == 'download_url') {
            var one = '<span class="download">&#9633;</span>'
            out += one

        } else if (links[d]['type'] == 'landing_url') {
            var one = '<span class="landing">&#9633;</span>'
            out += one

        } else if (links[d]['type'] == 'other_url') {
            var one = '<span class="other">&#9633;</span>'
            out += one

        }

    }
    return out;

}


function link2tooltip(text, links) {

    var sample = '<span class="tooltip" title="Tooltip">';
    var lastPart = '</span>';
    for (var d = 0; d < links.length; d++) {
        var one = '<input type="checkbox" value="keep" class="keep" checked></input><a href='+links[d].href+'>'+links[d].name+'</a><br>';
        sample += one;
    }
    var out = sample+lastPart;
    return out;


}


function makeForm(links) {
    var sample = '<form class="links">';
    var lastPart = '</form>';
    for (var d = 0; d < links.length; d++) {
        var one = '<input type="checkbox" value="keep" class="keep" checked></input><a href='+links[d].href+'>'+links[d].name+'</a><br>';
        sample += one;
    }
    var out = sample+lastPart;
    return out;
}


var markOptionsQuote = {
    "separateWordSearch": false,
    "className": "quote"
};
var markOptionsRef = {
    "className": "ref",
    "separateWordSearch": false
};

$(document).ready(function(){

    console.log('processing.js');
    console.log(data);
    console.log(results);
    //console.log(combined.bib_and_links.length);
    var start = 0;


    // REVERSE/REWRITE
    for (var d = 0; d < combined.bib_and_links.length; d++) {

        var obj = combined.bib_and_links[d];
        var match = obj.match;
        var searchResults = obj.search_results;
        //console.log(searchResults);

        if(typeof searchResults !== 'undefined') {
            var links = obj.search_results[0].bibjson[0].link;
        }


        if (typeof match !== 'undefined') {
            //console.log(match);
            //var adjust = 14;
            var part = text.slice(start, obj.match.end);
            //console.log(part+" SUCCESS ");
            start = obj.match.end;
            // console.log(obj);

            if (searchResults) {
                var links = searchResults[0].bibjson[0].link;
                var quote = match.groups.works[0].quote;
                //console.log(quote)
                var all = match.groups.all;
            }
        }

        if(links) {
            //console.log(links);
            //$(".textdisplay").append(part+addMenu());
            //$(".textdisplay").append(part+link2color(links));
            $(".textdisplay").append(part+makeForm(links));
        } else {
            $(".textdisplay").append(part);
        }

        if (typeof quote !== 'undefined') {
            //console.log(quote);
            $(".textdisplay").mark(quote, markOptionsQuote);
        }

        if (typeof all !== 'undefined') {
            //console.log(all);
            $(".textdisplay").mark(all, markOptionsRef);
        }

        //reset (for some js reason)
        //searchResults = 'undefined';
        links = '';

        // quote = 'undefined';
        // all = 'undefined';

    }


    // for (var d = 0; d < combined.bib_and_links.length; d++) {
    //
    //     var obj = combined.bib_and_links[d];
    //
    //     if(typeof obj.search_results != 'undefined') {
    //         var links = obj.search_results[0].bibjson[0].link;
    //     }
    //
    //     if(typeof links != 'undefined') {
    //         console.log(links);
    //         var colorCoded = link2color(links);
    //     }
    //
    //
    //
    //     if (typeof(obj.match) != 'undefined') {
    //         //var adjust = 14;
    //         var part = text.slice(start, obj.match.end);
    //         //console.log(part+" SUCCESS ");
    //         start = obj.match.end;
    //         // console.log(obj);
    //         var quote = obj.match.groups.works[0].quote;
    //
    //         var all = obj.match.groups.all;
    //     }
    //
    //
    //     //append the constructed thing to textdisplay
    //     // if(typeof part != 'undefined') {
    //     //     $(".textdisplay").append(part+addCheckbox());
    //     // }
    //     if(typeof links != 'undefined') {
    //         $(".textdisplay").append(part+link2color(links));
    //     }
    //
    //     if (typeof quote !== 'undefined') {
    //         $(".textdisplay").mark(quote, markOptionsQuote);
    //     }
    //
    //     if (typeof all !== 'undefined') {
    //         $(".textdisplay").mark(all, markOptionsRef);
    //     }
    //
    // }




    // will have to append the rest of the text here based on the last slice (part)



});
