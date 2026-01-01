function formatDate(dateString) {
  if (!dateString) return "";
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

async function loadStories() {
  const response = await fetch("config.json");
  const config = await response.json();

  document.getElementById("stories-container").innerHTML = config.stories
    .map(
      (story) => /* html */ `
        <div class="col-md-6 col-lg-4">
          <a href="${story.link}" class="card h-100 shadow-sm text-decoration-none story-card">
            <img src="${story.screenshot}"
                 class="card-img-top"
                 alt="${story.title}"
                 style="height: 200px; object-fit: cover;">
            <div class="card-body d-flex flex-column">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <h5 class="card-title mb-0 flex-grow-1">${story.title}</h5>
              </div>
              <div class="d-flex gap-2 mb-2 text-muted small">
                ${story.date ? `<span class="story-date">${formatDate(story.date)}</span>` : ""}
                ${story.folder ? `<span class="story-folder">/${story.folder}</span>` : ""}
              </div>
              <p class="card-text flex-grow-1">${story.description}</p>
            </div>
          </a>
        </div>
    `,
    )
    .join("");
}

document.addEventListener("DOMContentLoaded", loadStories);
