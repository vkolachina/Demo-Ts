function helloWorld(name: string = "World"): string {
    return `Hello, ${name}! Welcome to TypeScript.`;
}

console.log(helloWorld());
console.log(helloWorld("GitHub Actions"));