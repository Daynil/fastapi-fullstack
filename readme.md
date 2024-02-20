## FastAPI, HTMX, and pocketbase as a local, fullstack framework

Conceptually, I wanted to see if there was a good way to eliminate the fragmented approach of having a separate front
end and back end code base.

While I partly solved this problem on my last iteration by leveraging pocketbase as my only backend framework, since all
of the pages were rendered with react and the data is transmitted as JSON, most of my app's code ends up being
synchronizing front and backend state. `react-query` certainly helps with this, but you still have to write a bunch of
boilerplate for every function to wrap it in react-query, and it is difficult to keep in your head.

HTMX, used with jinja2, is the solution to this here. Now, the frontend is just the browser itself, which renders
hypermedia sent by the server. Any state synchronizing happens directly on the server. Client side code is almost
entirely eliminated except for sprinkles of interactivity.

By leveraging a combination of static files built to a generated directory and a set of dynamic routes which generate
html on the fly, I can get the best of both client and server rendering in one simple app. The static routes can be
cached on a CDN to allow effectively unlimited traffic at almost no cost, and only the dynamic routes that need to allow
app functionality are rendered on the fly.

The cost of generating html on the fly should be effectively the same as generating the same json for a frontend-heavy
implementation since the same data is generated on each, just in a different format.

## Usage

`app` is the directory with all source files, including jinja2 templates and partials. `app/templates/to_pregenerate` is
a folder which contains all of my fully static pages, which are built by my build process and, along with all static
files like css and libraries, are placed in `generated`.

FastAPI mounts the `generated` folder to `/`, so all requests for these static files resolve as normal in the
browser. All dynamic routes and api routes are mounted to FastAPI under the `/app/` subdirectory, e.g. `/app/books`.
These dynamic calls have their templates generated on the server on the fly and returned to the client.

Activate the python environment before running the server with `$ conda activate ./env` (can use `mamba` for all this as usual). This environment can be recreated from the `requirements.txt` file with:

```shell
# While in base project dir
$ conda create --prefix ./env python=3.11
$ python -m pip install -r requirements.txt
$ conda activate ./env
```

Pocketbase automatically applies any unapplied migrations inside `./app/pocketbase/pb_migrations` on serve, so the schema is reflected automatically. Any prior data would need to be brought back in by import.

`$ ./dev-build.sh` starts the pocketbase server, and starts a watcher (using `watchexec`) for my app directory, and on changes, restarts
both my static build process and the `unicorn` FastAPI server.


## Pearls

### Caching

Be aware of browser caching of the static assets and files. During development, it's best to turn off caching in dev tools (network tab checkbox at the top) so you don't have to worry about whether the issue is due to stale assets. However, keep in mind the cache is only disabled while the devtools are open.


### Statically Generated Pages

Keep in mind that the statically generated pages (marketing routes, blog, etc.) do not have access to the request object unless/until they make a call to the server.

This creates a bit of a catch 22 with an "app" style site, where I want to present a header that depends on whether the user is logged in. For static pages, we can make a quick on-load call with HTMX to check logged in status and swap out only auth menu. All dynamic pages will already have access to the request object, so we just serve it directly.


### Template Architecture

Since we're using HTMX, we want to be able to swap out small bits of content where needed. 

For dynamic pages, each "page" should have a complete "page" template, which includes the layout and all the content.

Any content which may be swapped out during usage *and is reused multiple times* should get its own component template with a macro.

If the content may be swapped out during usage, but we don't reuse it (e.g. a form like in books/page.jinja), we can use blocks as template fragments. One caveat: any imports used within the block must be imported within the block.

Usually, if there's an error on a page or in a component, in the context we can either pass null error to indicate no error, or the error object. Anywhere in the template that needs to display an error can just check for presence of the error object. The granularity of where the error is passed depends on the context. So if we have a form component within a page, the form submission would post to a route that returns just the form component, which may or may not have an error in the context.

If there's an error on a page where a success is a redirect (e.g. login), we can just use htmx to swap in the error to an id like `#error`.


### Updating content outside of the hx-target

[Other Content](https://htmx.org/examples/update-other-content/#events)

This situation comes up often and is hard to grasp at first. Ultimately, Solution #3 with events is my favorite from teh article. We do whatever swap we need to, and if we want to update something else, we just pass down an event from the server, which triggers another request on a different object. See my add book form in `books/page.jinja` and `books/book_list.jinja\`.



## TODO

Need to set up `.env` file and ingest it in settings.
https://github.com/Mateko/FastAPI-boilerplate/blob/main/app/settings/core.py

Add CLI for faster access to common scripts.

Next:
switch to tailwind, pinesui, and use alpine where needed