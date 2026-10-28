using System.Collections.Concurrent;
using System.ComponentModel.DataAnnotations;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();

var menu = new[]
{
    new MenuItem("01", "Burrata & stone fruit", "Heirloom tomato, ripe peach, basil oil, grilled sourdough.", "Starters", 16, "🍅", true),
    new MenuItem("02", "Wild mushroom toast", "Whipped ricotta, woodland mushrooms, thyme, a little honey.", "Starters", 15, "🍄", true),
    new MenuItem("03", "Hand-cut pappardelle", "Slow-braised short rib, red wine sugo, parmesan, fresh herbs.", "Mains", 29, "🍝", false),
    new MenuItem("04", "The garden bowl", "Warm grains, roasted squash, crisp greens, tahini-lemon dressing.", "Mains", 23, "🥗", true),
    new MenuItem("05", "Crispy-skin salmon", "Spring peas, butter beans, dill crème fraîche, charred lemon.", "Mains", 31, "🐟", false),
    new MenuItem("06", "Olive oil cake", "Citrus-soaked cake, seasonal berries, soft vanilla cream.", "Dessert", 12, "🍰", true),
};
var reservations = new ConcurrentBag<Reservation>();

app.MapGet("/api/menu", () => Results.Ok(menu));

app.MapPost("/api/reservations", (ReservationRequest request) =>
{
    var errors = new Dictionary<string, string[]>();
    var name = request.Name?.Trim() ?? "";
    var email = request.Email?.Trim() ?? "";
    if (name.Length is < 2 or > 80)
        errors["name"] = ["Please enter a name between 2 and 80 characters."];
    if (!new EmailAddressAttribute().IsValid(email))
        errors["email"] = ["Please enter a valid email address."];
    if (!DateOnly.TryParse(request.Date, out var date) || date < DateOnly.FromDateTime(DateTime.Today))
        errors["date"] = ["Please choose today or a future date."];
    if (!TimeOnly.TryParse(request.Time, out _))
        errors["time"] = ["Please choose a valid reservation time."];
    if (request.Guests is < 1 or > 12)
        errors["guests"] = ["Reservations are available for 1 to 12 guests."];

    if (errors.Count > 0)
        return Results.ValidationProblem(errors);

    var reservation = new Reservation(
        Convert.ToHexString(Guid.NewGuid().ToByteArray())[..6],
        name, email, date, request.Time!, request.Guests);
    reservations.Add(reservation);
    return Results.Created($"/api/reservations/{reservation.Confirmation}", reservation);
});

app.MapFallbackToFile("index.html");
app.Run();

record MenuItem(string Id, string Name, string Description, string Category, decimal Price, string Emoji, bool Vegetarian);
record ReservationRequest(string? Name, string? Email, string? Date, string? Time, int Guests);
record Reservation(string Confirmation, string Name, string Email, DateOnly Date, string Time, int Guests);
