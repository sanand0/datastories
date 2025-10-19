async function loadStories() {
  const response = await fetch("config.json");
  const config = await response.json();

  document.getElementById("stories-container").innerHTML = config.stories
    .map(
      (story) => /* html */ `
        <div class="col-md-6 col-lg-4">
          <a href="${story.link}" class="card h-100 shadow-sm text-decoration-none">
            <img src="${story.screenshot}"
                 class="card-img-top"
                 alt="${story.title}"
                 style="height: 200px; object-fit: contain;">
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">${story.title}</h5>
              <p class="card-text flex-grow-1">${story.description}</p>
            </div>
          </a>
        </div>
    `,
    )
    .join("");
}

document.addEventListener("DOMContentLoaded", loadStories);
