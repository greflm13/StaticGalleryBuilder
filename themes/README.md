# Custom CSS Themes

You can create custom Themes. They must at least include the following:

## Requirements for Themes

### Required Variables

Define the following variables in your theme:

- `--color1`: Primary color
- `--color2`: Secondary color
- `--color3`: Additional color
- `--color4`: Another color

These variables are essential for automatic icon generation.

### Folder Icon Specification

Include the following CSS rule to specify the folder icon used in your theme:

```css
.foldericon {
  content: url("data:image/svg+xml,%3Csvg width='800px' height='800px' viewBox='0 0 1024 1024' class='icon' version='1.1' xmlns='http://www.w3.org/2000/svg' fill='%23000000'%3E%3Cg id='SVGRepo_bgCarrier' stroke-width='0' /%3E%3Cg id='SVGRepo_tracerCarrier' stroke-linecap='round' stroke-linejoin='round' /%3E%3Cg id='SVGRepo_iconCarrier'%3E%3Cpath d='M853.333333 256H469.333333l-85.333333-85.333333H170.666667c-46.933333 0-85.333333 38.4-85.333334 85.333333v170.666667h853.333334v-85.333334c0-46.933333-38.4-85.333333-85.333334-85.333333z' fill='%233674e7' /%3E%3Cpath d='M853.333333 256H170.666667c-46.933333 0-85.333333 38.4-85.333334 85.333333v426.666667c0 46.933333 38.4 85.333333 85.333334 85.333333h682.666666c46.933333 0 85.333333-38.4 85.333334-85.333333V341.333333c0-46.933333-38.4-85.333333-85.333334-85.333333z' fill='%236495ed' /%3E%3C/g%3E%3C/svg%3E");
}
```

Replace the SVG data URI (`url("data:image/svg+xml,...")`) with your desired SVG icon content.

## Previews of included themes

### alpenglow

![alpenglow](screenshots/alpenglow.png)

### aritim-dark

![aritim-dark](screenshots/aritim-dark.png)

### aritim

![aritim](screenshots/aritim.png)

### autumn

![autumn](screenshots/autumn.png)

### carnation

![carnation](screenshots/carnation.png)

### catpuccin

![catpuccin](screenshots/catpuccin.png)

### cornflower

![cornflower](screenshots/cornflower.png)

### default-dark

![default-dark](screenshots/default-dark.png)

### default

![default](screenshots/default.png)

### ivy

![ivy](screenshots/ivy.png)

### kjoe

![kjoe](screenshots/kjoe.png)

### monokai-vibrant

![monokai-vibrant](screenshots/monokai-vibrant.png)

### rainbow

![rainbow](screenshots/rainbow.png)

### spring

![spring](screenshots/spring.png)

### steam

![steam](screenshots/steam.png)

### summer

![summer](screenshots/summer.png)

### sunflower

![sunflower](screenshots/sunflower.png)

### winter

![winter](screenshots/winter.png)
