async function loadStories() {
  const response = await fetch("config.json");
  const config = await response.json();

  const container = document.getElementById("stories-container");

  const cardsHTML = config.stories
    .map(
      (story) => /* html */ `
        <div class="col-md-6 col-lg-4">
          <div class="card h-100 shadow-sm"
               style="cursor: pointer;"
               onclick="window.location.href='${story.link}'">
            <img src="${story.screenshot}"
                 class="card-img-top"
                 alt="${story.title}"
                 style="height: 200px; object-fit: cover;">
            <div class="card-body d-flex flex-column">
              <h5 class="card-title">${story.title}</h5>
              <p class="card-text flex-grow-1">${story.description}</p>
            </div>
          </div>
        </div>
    `
    )
    .join("");

  container.replaceChildren();
  container.insertAdjacentHTML("beforeend", cardsHTML);
}

document.addEventListener("DOMContentLoaded", loadStories);
