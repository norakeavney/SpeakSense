'use client';

import React, { useEffect, useRef } from "react";
import cloud from "d3-cloud";

export default function WordCloud({ words = [] }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!words || words.length === 0) return;

    const formatted = words.map(w => ({
      text: w.word || w,
      size: w.score ? 20 + w.score * 60 : 20,
    }));

    const layout = cloud()
      .size([600, 300])
      .words(formatted)
      .padding(5)
      .rotate(() => (Math.random() > 0.5 ? 0 : 0)) // keep horizontal for clean look
      .font("Inter, sans-serif")
      .fontSize(d => d.size)
      .on("end", draw);

    layout.start();

    function draw(words) {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove(); // clear previous

      svg
        .attr("width", 600)
        .attr("height", 300)
        .append("g")
        .attr("transform", "translate(300,150)")
        .selectAll("text")
        .data(words)
        .enter()
        .append("text")
        .style("font-size", d => `${d.size}px`)
        .style("fill", "#3b82f6")
        .attr("text-anchor", "middle")
        .attr("transform", d => `translate(${d.x},${d.y})`)
        .text(d => d.text);
    }
  }, [words]);

  return (
    <svg ref={svgRef}></svg>
  );
}