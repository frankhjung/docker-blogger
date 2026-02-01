# Publishing to Blogspot

## Intention

This is an outline of the requirements for publishing to blogspot from a local
source. The intention is to be able to publish an article (either markdown or
HTML) to my blogspot account. I will use the [API
v3](https://developers.google.com/blogger/docs/3.0/using) to do this.

## Outline

1. Use existing blogspot account (frankhjung@gmail.com).
1. Assume the blog has been created in a local GitHub repository.
1. Assume the GitHub repository has a GitHub pipeline that renders the source
   (markdown) into HTML.

My objective is to:

1. add a GitHub action to the blog repository.
1. This action will use the blogspot API to publish the blog to the blogspot.
1. The information required by the API will be provided by the GitHub action as
   parameters.
1. Minimal parameters are:
   * blogspot post title
   * blogspot URL
   * blogspot blog ID
   * blogspot API key
   * blogspot label(s)
   The blog will be published to the blogspot account using the API.
   The blog will be in "draft" mode
1. The GitHub action will use the API to publish the blog.
1. The GitHub action will be coded in Python.
1. The GitHub action will be published to GitHub Container Registry.

## Notes

* The Python project will use uv and ruff with pytest unit tests.
* The Python project will be published to GitHub Container Registry.
* Ensure the project adheres to GitHub standards

## References

* [Blogger API](https://developers.google.com/blogger/docs/3.0/using)
* [GitHub Actions](https://github.com/actions)
* [uv](https://docs.astral.sh/uv/)
* [ruff](https://docs.astral.sh/ruff/)
* [pytest](https://docs.astral.sh/pytest/)
