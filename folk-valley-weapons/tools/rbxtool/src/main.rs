//! rbxtool: convert Roblox binary models to JSON and back.
//!   rbxtool dump  <in.rbxm|in.rbxmx> <out.json>
//!   rbxtool build <in.json> <out.rbxm> [out.rbxmx]
//! JSON is a list of nodes {class, name, ref, props, children}; property values use
//! rbx_types' serde form ({"Vector3":[x,y,z]}, {"Ref":"<32 hex>"}, ...).
use std::collections::BTreeMap;
use std::fs::File;
use std::io::{BufReader, BufWriter};

use anyhow::{bail, Context, Result};
use rbx_dom_weak::types::{Ref, Variant};
use rbx_dom_weak::{InstanceBuilder, WeakDom};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct Node {
    class: String,
    name: String,
    #[serde(rename = "ref")]
    referent: Ref,
    #[serde(default)]
    props: BTreeMap<String, Variant>,
    #[serde(default)]
    children: Vec<Node>,
}

fn dump_node(dom: &WeakDom, r: Ref) -> Node {
    let inst = dom.get_by_ref(r).unwrap();
    Node {
        class: inst.class.to_string(),
        name: inst.name.clone(),
        referent: r,
        props: inst
            .properties
            .iter()
            .map(|(k, v)| (k.to_string(), v.clone()))
            .collect(),
        children: inst.children().iter().map(|c| dump_node(dom, *c)).collect(),
    }
}

fn build_node(n: Node) -> InstanceBuilder {
    let mut b = InstanceBuilder::new(n.class.as_str())
        .with_name(n.name)
        .with_referent(n.referent);
    for (k, v) in n.props {
        b.add_property(k.as_str(), v);
    }
    for c in n.children {
        b.add_child(build_node(c));
    }
    b
}

fn read_dom(path: &str) -> Result<WeakDom> {
    let f = BufReader::new(File::open(path).with_context(|| path.to_string())?);
    Ok(if path.ends_with(".rbxmx") || path.ends_with(".rbxlx") {
        rbx_xml::from_reader_default(f)?
    } else {
        rbx_binary::from_reader(f)?
    })
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("dump") => {
            let dom = read_dom(&args[2])?;
            let nodes: Vec<Node> = dom
                .root()
                .children()
                .iter()
                .map(|c| dump_node(&dom, *c))
                .collect();
            serde_json::to_writer_pretty(BufWriter::new(File::create(&args[3])?), &nodes)?;
        }
        Some("build") => {
            let nodes: Vec<Node> =
                serde_json::from_reader(BufReader::new(File::open(&args[2])?))?;
            let mut dom = WeakDom::new(InstanceBuilder::new("DataModel"));
            let root = dom.root_ref();
            let tops: Vec<Ref> = nodes
                .into_iter()
                .map(|n| dom.insert(root, build_node(n)))
                .collect();
            rbx_binary::to_writer(BufWriter::new(File::create(&args[3])?), &dom, &tops)?;
            if let Some(xml) = args.get(4) {
                rbx_xml::to_writer_default(BufWriter::new(File::create(xml)?), &dom, &tops)?;
            }
        }
        _ => bail!("usage: rbxtool dump <in> <out.json> | build <in.json> <out.rbxm> [out.rbxmx]"),
    }
    Ok(())
}
