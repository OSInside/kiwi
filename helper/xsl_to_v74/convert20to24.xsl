<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv20to24">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv20to24"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemeversion</tag>
    from <literal>2.0</literal> to <literal>2.4</literal>. 
</para>
<xsl:template match="image" mode="conv20to24">
    <xsl:choose>
        <!-- nothing to do if already at 2.4 -->
        <xsl:when test="@schemeversion > 2.0 or @schemaversion > 2.0">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemeversion="2.4">
                <xsl:copy-of select="@*[local-name() != 'schemeversion']"/>
                <xsl:apply-templates mode="conv20to24"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv20to24">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv20to24"/>
    </xsl:copy>
</xsl:template>

<!-- remove attributes and add info -->
<para xmlns="http://docbook.org/ns/docbook">
    Remove attributes memory,disk,HWversion,guestOS_32Bit and guestOS_64Bit
    from the <literal>2.0</literal> packages type [vmware|xen] version.
    This information needs to be provided by an additional
    <tag class="element">vmwareconfig</tag> or
    <tag class="element">xenconfig</tag> element
</para>
<xsl:template match="packages" mode="conv20to24">
    <packages>
    <xsl:if test="@memory or 
        @disk or 
        @HWversion or 
        @guestOS_32Bit or 
        @guestOS_64Bit">
    <xsl:message>
        <xsl:text>NOTE: You need to setup a vmwareconfig and/or&#10;</xsl:text>
        <xsl:text>      xenconfig section in order to setup an&#10;</xsl:text>
        <xsl:text>      appropriate guest configuration. For&#10;</xsl:text>
        <xsl:text>      details see the 'KIWI image description'&#10;</xsl:text>
        <xsl:text>      chapter of the kiwi cookbook</xsl:text>
    </xsl:message>
    </xsl:if>
    <xsl:copy-of select="@*[not(local-name(.) = 'memory' or
        local-name(.) = 'disk' or
        local-name(.) = 'HWversion' or
        local-name(.) = 'guestOS_32Bit' or
        local-name(.) = 'guestOS_64Bit')]"/>
    <xsl:apply-templates mode="conv20to24"/>
    </packages>
</xsl:template>

</xsl:stylesheet>
