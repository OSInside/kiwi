<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        xmlns:exslt="http://exslt.org/common"
        exclude-result-prefixes="exslt"
>

<xsl:import href="include.xsl"/>
<xsl:import href="convert14to20.xsl"/>
<xsl:import href="convert20to24.xsl"/>
<xsl:import href="convert24to35.xsl"/>
<xsl:import href="convert35to37.xsl"/>
<xsl:import href="convert37to38.xsl"/>
<xsl:import href="convert38to39.xsl"/>
<xsl:import href="convert39to41.xsl"/>
<xsl:import href="convert41to42.xsl"/>
<xsl:import href="convert42to43.xsl"/>
<xsl:import href="convert43to44.xsl"/>
<xsl:import href="convert44to45.xsl"/>
<xsl:import href="convert45to46.xsl"/>
<xsl:import href="convert46to47.xsl"/>
<xsl:import href="convert47to48.xsl"/>
<xsl:import href="convert48to49.xsl"/>
<xsl:import href="convert49to50.xsl"/>
<xsl:import href="convert50to51.xsl"/>
<xsl:import href="convert51to52.xsl"/>
<xsl:import href="convert52to53.xsl"/>
<xsl:import href="convert53to54.xsl"/>
<xsl:import href="convert54to55.xsl"/>
<xsl:import href="convert55to56.xsl"/>
<xsl:import href="convert56to57.xsl"/>
<xsl:import href="convert57to58.xsl"/>
<xsl:import href="convert58to59.xsl"/>
<xsl:import href="convert59to60.xsl"/>
<xsl:import href="convert60to61.xsl"/>
<xsl:import href="convert61to62.xsl"/>
<xsl:import href="convert62to63.xsl"/>
<xsl:import href="convert63to64.xsl"/>
<xsl:import href="convert64to65.xsl"/>
<xsl:import href="convert65to66.xsl"/>
<xsl:import href="convert66to67.xsl"/>
<xsl:import href="convert67to68.xsl"/>
<xsl:import href="convert68to69.xsl"/>
<xsl:import href="convert69to70.xsl"/>
<xsl:import href="convert70to71.xsl"/>
<xsl:import href="convert71to72.xsl"/>
<xsl:import href="convert72to73.xsl"/>
<xsl:import href="convert73to74.xsl"/>
<xsl:import href="pretty.xsl"/>

<xsl:output encoding="utf-8" indent="yes"/>

<xsl:template match="/">
    <xsl:variable name="preprocess">
        <xsl:apply-templates select="/" mode="include"/>
    </xsl:variable>

    <xsl:variable name="v14">
        <xsl:apply-templates select="exslt:node-set($preprocess)" mode="conv14to20"/>
    </xsl:variable>

    <xsl:variable name="v20">
        <xsl:apply-templates select="exslt:node-set($v14)" mode="conv20to24"/>
    </xsl:variable>

    <xsl:variable name="v35">
        <xsl:apply-templates select="exslt:node-set($v20)" mode="conv24to35"/>
    </xsl:variable>

    <xsl:variable name="v37">
        <xsl:apply-templates select="exslt:node-set($v35)" mode="conv35to37"/>
    </xsl:variable>

    <xsl:variable name="v38">
        <xsl:apply-templates select="exslt:node-set($v37)" mode="conv37to38"/>
    </xsl:variable>

    <xsl:variable name="v39">
        <xsl:apply-templates select="exslt:node-set($v38)" mode="conv38to39"/>
    </xsl:variable>

    <xsl:variable name="v41">
        <xsl:apply-templates select="exslt:node-set($v39)" mode="conv39to41"/>
    </xsl:variable>

    <xsl:variable name="v42">
        <xsl:apply-templates select="exslt:node-set($v41)" mode="conv41to42"/>
    </xsl:variable>

    <xsl:variable name="v43">
        <xsl:apply-templates select="exslt:node-set($v42)" mode="conv42to43"/>
    </xsl:variable>

    <xsl:variable name="v44">
        <xsl:apply-templates select="exslt:node-set($v43)" mode="conv43to44"/>
    </xsl:variable>

    <xsl:variable name="v45">
        <xsl:apply-templates select="exslt:node-set($v44)" mode="conv44to45"/>
    </xsl:variable>

    <xsl:variable name="v46">
        <xsl:apply-templates select="exslt:node-set($v45)" mode="conv45to46"/>
    </xsl:variable>

    <xsl:variable name="v47">
        <xsl:apply-templates select="exslt:node-set($v46)" mode="conv46to47"/>
    </xsl:variable>

    <xsl:variable name="v48">
        <xsl:apply-templates select="exslt:node-set($v47)" mode="conv47to48"/>
    </xsl:variable>

    <xsl:variable name="v49">
        <xsl:apply-templates select="exslt:node-set($v48)" mode="conv48to49"/>
    </xsl:variable>

    <xsl:variable name="v50">
        <xsl:apply-templates select="exslt:node-set($v49)" mode="conv49to50"/>
    </xsl:variable>

    <xsl:variable name="v51">
        <xsl:apply-templates select="exslt:node-set($v50)" mode="conv50to51"/>
    </xsl:variable>

    <xsl:variable name="v52">
        <xsl:apply-templates select="exslt:node-set($v51)" mode="conv51to52"/>
    </xsl:variable>

    <xsl:variable name="v53">
        <xsl:apply-templates select="exslt:node-set($v52)" mode="conv52to53"/>
    </xsl:variable>

    <xsl:variable name="v54">
        <xsl:apply-templates select="exslt:node-set($v53)" mode="conv53to54"/>
    </xsl:variable>

    <xsl:variable name="v55">
        <xsl:apply-templates select="exslt:node-set($v54)" mode="conv54to55"/>
    </xsl:variable>

    <xsl:variable name="v56">
        <xsl:apply-templates select="exslt:node-set($v55)" mode="conv55to56"/>
    </xsl:variable>

    <xsl:variable name="v57">
        <xsl:apply-templates select="exslt:node-set($v56)" mode="conv56to57"/>
    </xsl:variable>

    <xsl:variable name="v58">
        <xsl:apply-templates select="exslt:node-set($v57)" mode="conv57to58"/>
    </xsl:variable>

    <xsl:variable name="v59">
        <xsl:apply-templates select="exslt:node-set($v58)" mode="conv58to59"/>
    </xsl:variable>

    <xsl:variable name="v60">
        <xsl:apply-templates select="exslt:node-set($v59)" mode="conv59to60"/>
    </xsl:variable>

    <xsl:variable name="v61">
        <xsl:apply-templates select="exslt:node-set($v60)" mode="conv60to61"/>
    </xsl:variable>

    <xsl:variable name="v62">
        <xsl:apply-templates select="exslt:node-set($v61)" mode="conv61to62"/>
    </xsl:variable>

    <xsl:variable name="v63">
        <xsl:apply-templates select="exslt:node-set($v62)" mode="conv62to63"/>
    </xsl:variable>

    <xsl:variable name="v64">
        <xsl:apply-templates select="exslt:node-set($v63)" mode="conv63to64"/>
    </xsl:variable>

    <xsl:variable name="v65">
        <xsl:apply-templates select="exslt:node-set($v64)" mode="conv64to65"/>
    </xsl:variable>

    <xsl:variable name="v66">
        <xsl:apply-templates select="exslt:node-set($v65)" mode="conv65to66"/>
    </xsl:variable>

    <xsl:variable name="v67">
        <xsl:apply-templates select="exslt:node-set($v66)" mode="conv66to67"/>
    </xsl:variable>

    <xsl:variable name="v68">
        <xsl:apply-templates select="exslt:node-set($v67)" mode="conv67to68"/>
    </xsl:variable>

    <xsl:variable name="v69">
        <xsl:apply-templates select="exslt:node-set($v68)" mode="conv68to69"/>
    </xsl:variable>

    <xsl:variable name="v70">
        <xsl:apply-templates select="exslt:node-set($v69)" mode="conv69to70"/>
    </xsl:variable>

    <xsl:variable name="v71">
        <xsl:apply-templates select="exslt:node-set($v70)" mode="conv70to71"/>
    </xsl:variable>

    <xsl:variable name="v72">
        <xsl:apply-templates select="exslt:node-set($v71)" mode="conv71to72"/>
    </xsl:variable>

    <xsl:variable name="v73">
        <xsl:apply-templates select="exslt:node-set($v72)" mode="conv72to73"/>
    </xsl:variable>

    <xsl:variable name="v74">
        <xsl:apply-templates select="exslt:node-set($v73)" mode="conv73to74"/>
    </xsl:variable>

    <xsl:apply-templates
        select="exslt:node-set($v74)" mode="pretty"
    />
</xsl:template>

</xsl:stylesheet>
